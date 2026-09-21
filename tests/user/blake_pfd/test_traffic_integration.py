from pathlib import Path
from math import radians, sin

from PyQt6.QtGui import (
    QImage,
    QPainter,
)

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)
from pyefis.user.blake_pfd.stratux_reader import (
    StratuxState,
    TrafficTarget,
)
from pyefis.user.blake_pfd.core.traffic_geometry import (
    calculate_traffic_geometry,
)


def test_stratux_alert_traffic_reaches_full_pfd_render(
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

    widget.config.features.show_traffic = True
    widget.config.features.show_weather = False
    widget.config.stratux.enabled = True

    # Deterministic map scale so the expected
    # traffic-symbol position is known.
    widget.map_range_nm = 5.0

    own_lat = 39.363833
    own_lon = -84.522000
    own_alt = 1500.0

    target_lat = 39.363833
    target_lon = -84.478900
    target_alt = 1200.0

    widget.pfd.latitude_deg = own_lat
    widget.pfd.longitude_deg = own_lon
    widget.pfd.position_valid = True
    widget.pfd.pressure_alt_ft = own_alt

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

    traffic_state = StratuxState(
        ok=True,
        traffic=[
            TrafficTarget(
                callsign="ALERT1",
                latitude_deg=target_lat,
                longitude_deg=target_lon,
                pressure_alt_ft=target_alt,
                vertical_speed_fpm=-700.0,
                traffic_alert=True,
                position_valid=True,
            ),
        ],
        uplinks=[],
    )

    read_calls = 0

    def read_stratux():
        nonlocal read_calls

        read_calls += 1

        return traffic_state

    # Keep the production PFD/Stratux orchestration
    # intact while supplying deterministic receiver
    # data instead of a UDP socket.
    widget.stratux.read = read_stratux

    geometry = calculate_traffic_geometry(
        own_lat_deg=own_lat,
        own_lon_deg=own_lon,
        own_pressure_alt_ft=own_alt,
        target_lat_deg=target_lat,
        target_lon_deg=target_lon,
        target_pressure_alt_ft=target_alt,
    )

    assert geometry is not None
    assert geometry.distance_nm < widget.map_range_nm

    # Same production local-map geometry used by
    # draw_traffic_overlay().
    box_x = 10
    box_y = 430
    box_w = 160
    box_h = 130

    center_x = (
        box_x
        + box_w / 2.0
    )

    center_y = (
        box_y
        + box_h / 2.0
    )

    radius = (
        min(
            box_w,
            box_h,
        )
        * 0.42
    )

    reference_deg = float(
        widget.map_orientation_state.reference_deg
    )

    relative_bearing = (
        geometry.bearing_deg
        - reference_deg
    ) % 360.0

    angle = radians(
        relative_bearing
    )

    target_radius = (
        radius
        * min(
            1.0,
            geometry.distance_nm
            / widget.map_range_nm,
        )
    )

    expected_x = (
        center_x
        + sin(angle)
        * target_radius
    )

    expected_y = (
        center_y
        - cos(angle)
        * target_radius
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

    # Production render must read Stratux exactly
    # once during this paint cycle.
    assert read_calls == 1

    # Traffic alerts are rendered in production
    # yellow QColor(255, 220, 0). Search only near
    # the calculated target position.
    center_pixel_x = int(
        round(
            expected_x
        )
    )

    center_pixel_y = int(
        round(
            expected_y
        )
    )

    alert_pixel_found = False

    for y in range(
        max(
            0,
            center_pixel_y - 10,
        ),
        min(
            image.height(),
            center_pixel_y + 11,
        ),
    ):
        for x in range(
            max(
                0,
                center_pixel_x - 10,
            ),
            min(
                image.width(),
                center_pixel_x + 11,
            ),
        ):
            color = image.pixelColor(
                x,
                y,
            )

            if (
                color.red() >= 230
                and color.green() >= 190
                and color.green() <= 240
                and color.blue() <= 50
            ):
                alert_pixel_found = True
                break

        if alert_pixel_found:
            break

    assert alert_pixel_found is True

    widget.close()
