from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtGui import QImage, QPainter

from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


@pytest.mark.parametrize(
    "stale_input, blocked_draw_methods",
    [
        (
            "attitude",
            (
                "draw_attitude",
                "draw_heading_strip",
                "draw_hsi_compass_rose",
                "draw_turn_and_slip",
                "draw_synthetic_vision",
                "draw_hits_guidance",
                "draw_flight_director",
                "draw_flight_path_marker",
            ),
        ),
        (
            "air_data",
            (
                "draw_airspeed_tape",
                "draw_altitude_tape",
                "draw_vsi",
                "draw_synthetic_vision",
                "draw_hits_guidance",
                "draw_flight_director",
                "draw_flight_path_marker",
            ),
        ),
        (
            "position",
            (
                "draw_hsi_compass_rose",
                "draw_synthetic_vision",
                "draw_hits_guidance",
                "draw_flight_director",
                "draw_flight_path_marker",
            ),
        ),
    ],
)
def test_stale_primary_data_is_not_drawn(
    qtbot,
    qapp,
    tmp_path: Path,
    stale_input: str,
    blocked_draw_methods: tuple[str, ...],
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=tmp_path / "baro.json",
    )
    widget.timer.stop()
    qtbot.addWidget(widget)
    widget.resize(1024, 600)
    widget.update_data()

    assert widget.pfd is not None

    widget.config.features.show_attitude = True
    widget.config.features.show_heading = True
    widget.config.features.show_hsi = True
    widget.config.features.show_turn_rate = True
    widget.config.features.show_airspeed = True
    widget.config.features.show_altitude = True
    widget.config.features.show_vsi = True
    widget.config.features.show_synthetic_vision = True
    widget.config.features.show_traffic = False
    widget.config.features.show_weather = False
    from dataclasses import replace
    widget.guidance_touch_settings = replace(
        widget.guidance_touch_settings,
        synthetic_vision_enabled=True,
        hits_enabled=True,
        flight_director_enabled=True,
        flight_path_marker_enabled=True,
    )

    watchdog = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=stale_input != "position",
        attitude_valid=True,
        attitude_fresh=stale_input != "attitude",
        air_data_valid=True,
        air_data_fresh=stale_input != "air_data",
    )
    widget.sensor_watchdog_state = watchdog

    assert watchdog.degraded is True

    image = QImage(
        1024,
        600,
        QImage.Format.Format_ARGB32,
    )
    image.fill(0)

    with ExitStack() as stack:
        call_counts = {
            method: 0
            for method in blocked_draw_methods
        }

        def make_spy(method, original):
            def spy(*args, **kwargs):
                call_counts[method] += 1
                return original(*args, **kwargs)

            return spy

        for method in blocked_draw_methods:
            original = getattr(widget, method)
            stack.enter_context(
                patch.object(
                    widget,
                    method,
                    new=make_spy(method, original),
                )
            )

        painter = QPainter(image)
        try:
            widget.render(painter)
        finally:
            painter.end()

        assert image.isNull() is False

        for method in blocked_draw_methods:
            assert call_counts[method] == 0, method

        # Restore fresh inputs and verify that each
        # instrument's real drawing function runs.
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

        assert widget.sensor_watchdog_state.degraded is False

        recovered_image = QImage(
            1024,
            600,
            QImage.Format.Format_ARGB32,
        )
        recovered_image.fill(0)

        painter = QPainter(recovered_image)
        try:
            widget.render(painter)
        finally:
            painter.end()

        assert recovered_image.isNull() is False

        for method in blocked_draw_methods:
            assert call_counts[method] == 1, method

    widget.close()
    widget.deleteLater()
    qapp.processEvents()
