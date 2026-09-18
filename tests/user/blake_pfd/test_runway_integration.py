from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import (
    QPointF,
    Qt,
)
from PyQt6.QtGui import (
    QImage,
    QPainter,
    QPolygonF,
)

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)
from pyefis.user.blake_pfd.core.runway_projection import (
    RunwayProjectionComputer,
)


def test_khao_runway_reaches_full_pfd_render(
    qtbot,
    tmp_path: Path,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.resize(
        1024,
        600,
    )

    widget.update_data()

    assert widget.pfd is not None

    # Force the production synthetic-vision runway
    # path on while suppressing unrelated terrain
    # and obstacle graphics.
    widget.config.features.show_synthetic_vision = True
    widget.config.features.show_obstacles = False

    widget.guidance_touch_settings = replace(
        widget.guidance_touch_settings,
        synthetic_vision_enabled=True,
    )

    widget.real_terrain_enabled = False

    widget.config.navigation.selected_waypoint_id = (
        "KHAO"
    )

    runway = widget.database.best_runway(
        "KHAO"
    )

    assert runway is not None
    assert runway.airport_ident == "KHAO"

    real_projector = (
        RunwayProjectionComputer()
    )

    projection_calls = []

    class RecordingProjector:
        def project(
            self,
            **kwargs,
        ):
            result = real_projector.project(
                **kwargs
            )

            projection_calls.append(
                (
                    kwargs["geometry"],
                    result,
                )
            )

            return result

    widget.runway_projection_computer = (
        RecordingProjector()
    )

    # Position west of Butler County Regional,
    # looking generally east toward the runway.
    widget.pfd.position_valid = True
    widget.pfd.latitude_deg = 39.3638
    widget.pfd.longitude_deg = -84.5400
    widget.pfd.indicated_alt_ft = 1600.0
    widget.pfd.heading_deg = 92.0
    widget.pfd.pitch_deg = 0.0
    widget.pfd.roll_deg = 0.0

    widget.sensor_watchdog_state = (
        widget.sensor_watchdog.evaluate(
            flight_data_available=True,
            position_valid=True,
            position_fresh=True,
            attitude_valid=True,
            attitude_fresh=True,
            air_data_valid=True,
            air_data_fresh=True,
        )
    )

    image = QImage(
        1024,
        600,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.render(
            painter
        )

    finally:
        painter.end()

    assert image.isNull() is False

    # Full PFD render must have reached the
    # production runway projector exactly once.
    assert len(projection_calls) == 1

    geometry, projected = (
        projection_calls[0]
    )

    assert geometry.airport_ident == "KHAO"

    assert geometry.low_end.ident == "12"
    assert geometry.high_end.ident == "30"

    assert projected is not None
    assert projected.visible is True

    points = projected.polygon_points

    assert len(points) >= 3

    polygon = QPolygonF(
        [
            QPointF(
                point.x_px,
                point.y_px,
            )
            for point in points
        ]
    )

    bounds = (
        polygon
        .boundingRect()
        .toAlignedRect()
        .intersected(
            image.rect()
        )
    )

    assert bounds.isEmpty() is False

    # Production runway fill is QColor(45, 45, 45).
    # Verify actual rendered pixels inside the
    # projected runway polygon, rather than merely
    # proving that projection ran.
    runway_fill_pixels = 0

    for y in range(
        bounds.top(),
        bounds.bottom() + 1,
    ):
        for x in range(
            bounds.left(),
            bounds.right() + 1,
        ):
            if not polygon.containsPoint(
                QPointF(
                    x + 0.5,
                    y + 0.5,
                ),
                Qt.FillRule.OddEvenFill,
            ):
                continue

            color = image.pixelColor(
                x,
                y,
            )

            if (
                color.red() == 45
                and color.green() == 45
                and color.blue() == 45
            ):
                runway_fill_pixels += 1

                if runway_fill_pixels >= 5:
                    break

        if runway_fill_pixels >= 5:
            break

    assert runway_fill_pixels >= 5

    widget.close()
