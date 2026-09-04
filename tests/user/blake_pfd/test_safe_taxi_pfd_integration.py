from dataclasses import replace
from types import SimpleNamespace

from PyQt6.QtGui import QImage, QPainter

import pyefis.user.blake_pfd.pfd_demo as pfd_demo_module
from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.flight_computer import FlightData
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


LAT = 39.3638000488
LON = -84.5220031738
ELEV = 633.0


def make_flight(
    *,
    gs=0.0,
    ias=0.0,
    vsi=0.0,
):
    return FlightData(
        ias_kt=ias,
        tas_kt=ias,
        pressure_alt_ft=ELEV,
        indicated_alt_ft=ELEV,
        vsi_fpm=vsi,
        heading_deg=120.0,
        track_deg=120.0,
        ground_speed_kt=gs,
        latitude_deg=LAT,
        longitude_deg=LON,
        position_valid=True,
    )


def make_watchdog():
    return SimpleNamespace(
        position_valid=True,
        position_fresh=True,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
        degraded=False,
        failed=False,
        message="",
    )


def setup_widget(
    qapp,
    monkeypatch,
    *,
    auto=True,
):
    clock = [0.0]
    calls = []

    monkeypatch.setattr(
        pfd_demo_module,
        "monotonic",
        lambda: clock[0],
    )

    widget = BlakePfdDemo(
        use_hardware=False,
    )
    widget.timer.stop()
    widget.resize(1280, 720)
    widget.update_data()

    widget.config = replace(
        widget.config,
        features=replace(
            widget.config.features,
            show_safe_taxi=True,
        ),
        safe_taxi=replace(
            widget.config.safe_taxi,
            auto_switch_enabled=auto,
        ),
    )

    widget.sensor_watchdog_state = (
        make_watchdog()
    )

    widget.draw_safe_taxi_map = (
        lambda *args: calls.append(
            "SAFE_TAXI"
        )
    )

    widget.draw_touch_navigation = (
        lambda *args, **kwargs: None
    )

    widget.draw_warning_strip = (
        lambda *args, **kwargs: None
    )

    # Unrelated aircraft/engine diagnostic overlay.
    # Synthetic Safe Taxi integration states do not
    # populate a complete EngineState.
    widget.draw_aircraft_state_label = (
        lambda *args, **kwargs: None
    )

    return widget, clock, calls


def render(widget):
    image = QImage(
        1280,
        720,
        QImage.Format.Format_ARGB32,
    )
    image.fill(0)

    painter = QPainter(image)

    try:
        widget.render(painter)
    finally:
        painter.end()


def close_widget(
    widget,
    qapp,
):
    if widget.timer.isActive():
        widget.timer.stop()

    widget.close()
    widget.deleteLater()
    qapp.processEvents()


def set_state(
    widget,
    *,
    gs=0.0,
    ias=0.0,
    vsi=0.0,
    airborne=False,
    landing_roll=False,
):
    widget.pfd = make_flight(
        gs=gs,
        ias=ias,
        vsi=vsi,
    )

    widget.aircraft.flight_state.airborne = (
        airborne
    )

    widget.aircraft.flight_state.landing_roll = (
        landing_roll
    )


def test_stationary_startup_requires_eight_seconds(
    qapp,
    monkeypatch,
):
    widget, clock, calls = setup_widget(
        qapp,
        monkeypatch,
    )

    try:
        set_state(widget)

        clock[0] = 0.0
        render(widget)
        assert calls == []

        clock[0] = 7.9
        render(widget)
        assert calls == []

        clock[0] = 8.0
        render(widget)
        assert calls == ["SAFE_TAXI"]

    finally:
        close_widget(widget, qapp)


def test_slow_final_never_takes_over(
    qapp,
    monkeypatch,
):
    widget, clock, calls = setup_widget(
        qapp,
        monkeypatch,
    )

    try:
        set_state(
            widget,
            gs=90.0,
            ias=90.0,
            vsi=-300.0,
            airborne=True,
        )

        clock[0] = 0.0
        render(widget)

        for now in (
            10.0,
            13.0,
            20.0,
        ):
            set_state(
                widget,
                gs=20.0,
                ias=35.0,
                vsi=-250.0,
                airborne=False,
                landing_roll=True,
            )

            clock[0] = now
            render(widget)

        assert calls == []

    finally:
        close_widget(widget, qapp)


def test_post_landing_requires_three_seconds(
    qapp,
    monkeypatch,
):
    widget, clock, calls = setup_widget(
        qapp,
        monkeypatch,
    )

    try:
        set_state(
            widget,
            gs=90.0,
            ias=90.0,
            vsi=-400.0,
            airborne=True,
        )

        clock[0] = 0.0
        render(widget)

        set_state(
            widget,
            gs=20.0,
            ias=30.0,
            vsi=0.0,
            airborne=False,
            landing_roll=True,
        )

        clock[0] = 10.0
        render(widget)
        assert calls == []

        clock[0] = 12.9
        render(widget)
        assert calls == []

        clock[0] = 13.0
        render(widget)
        assert calls == ["SAFE_TAXI"]

    finally:
        close_widget(widget, qapp)


def test_auto_switch_false_still_blocks_takeover(
    qapp,
    monkeypatch,
):
    widget, clock, calls = setup_widget(
        qapp,
        monkeypatch,
        auto=False,
    )

    try:
        set_state(widget)

        clock[0] = 0.0
        render(widget)

        clock[0] = 8.0
        render(widget)

        assert calls == []

    finally:
        close_widget(widget, qapp)


def test_disk_config_remains_disarmed():
    assert (
        load_config()
        .safe_taxi
        .auto_switch_enabled
        is False
    )
