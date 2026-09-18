from dataclasses import replace
from pathlib import Path

from PyQt6.QtGui import QImage, QPainter

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurfaceGenerator,
)
from pyefis.user.blake_pfd.core.terrain_startup_validator import (
    TerrainStartupStatus,
)


def test_critical_terrain_reaches_full_pfd_render(
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

    # Establish normal runtime objects first.
    widget.update_data()

    assert widget.pfd is not None

    # Exercise synthetic terrain while keeping unrelated
    # obstacle graphics out of this render test.
    widget.config.features.show_synthetic_vision = True
    widget.config.features.show_obstacles = False

    widget.guidance_touch_settings = replace(
        widget.guidance_touch_settings,
        synthetic_vision_enabled=True,
    )

    # Use the real production terrain generator with a
    # deterministic elevation source.
    widget.synthetic_terrain_generator = (
        TerrainSurfaceGenerator(
            elevation_sampler=(
                lambda latitude, longitude: 1950.0
            ),
            forward_distances_nm=(
                0.125,
                0.25,
                0.5,
                1.0,
                2.0,
                3.0,
            ),
            lateral_fractions=(
                -1.0,
                -0.5,
                0.0,
                0.5,
                1.0,
            ),
            half_width_ratio=0.75,
        )
    )

    widget.real_terrain_enabled = True

    widget.terrain_startup_status = (
        TerrainStartupStatus(
            source_name="srtm",
            configured=True,
            directory_exists=True,
            tile_available=True,
            predictive_alerts_enabled=True,
            message="TEST TERRAIN READY",
            valid=True,
        )
    )

    # Aircraft only 50 ft above the deterministic
    # terrain, so the production visual classifier
    # must classify it CRITICAL.
    widget.pfd.position_valid = True
    widget.pfd.latitude_deg = 39.3638
    widget.pfd.longitude_deg = -84.5400
    widget.pfd.indicated_alt_ft = 2000.0
    widget.pfd.heading_deg = 0.0
    widget.pfd.pitch_deg = 0.0
    widget.pfd.roll_deg = 0.0
    widget.pfd.vsi_fpm = 0.0
    widget.pfd.ground_speed_kt = 120.0

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

    # Use the production refresh path to generate the
    # terrain surface consumed by the PFD renderer.
    widget.refresh_synthetic_terrain(
        1.0
    )

    assert (
        widget.synthetic_terrain_surface.valid
        is True
    )

    assert (
        len(
            widget.synthetic_terrain_surface
            .triangles
        )
        > 0
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

    # CRITICAL synthetic terrain is painted using the
    # production terrain color QColor(200, 0, 0).
    critical_pixels = 0

    for y in range(
        image.height()
    ):
        for x in range(
            image.width()
        ):
            color = image.pixelColor(
                x,
                y,
            )

            if (
                color.red() == 200
                and color.green() == 0
                and color.blue() == 0
            ):
                critical_pixels += 1

                if critical_pixels >= 20:
                    break

        if critical_pixels >= 20:
            break

    assert critical_pixels >= 20

    widget.close()
