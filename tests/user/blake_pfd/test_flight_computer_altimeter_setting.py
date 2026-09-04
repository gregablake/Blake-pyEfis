from types import SimpleNamespace

import pytest

from pyefis.user.blake_pfd.flight_computer import (
    FlightComputer,
)


def make_raw() -> SimpleNamespace:
    return SimpleNamespace(
        differential_pressure_pa=0.0,
        static_pressure_pa=101325.0,
        outside_air_temp_c=15.0,
        heading_deg=0.0,
        gps_track_deg=0.0,
        gps_ground_speed_kt=0.0,
        gps_lat_deg=39.3638,
        gps_lon_deg=-84.5220,
        yaw_rate_deg_s=0.0,
        accel_y_g=0.0,
        accel_z_g=1.0,
        desired_track_deg=0.0,
    )


def test_standard_setting_keeps_indicated_and_pressure_altitude_equal() -> None:
    computer = FlightComputer()

    computer.config.altitude.baro_setting_inhg = 29.92

    result = computer.update(make_raw())

    assert result.pressure_alt_ft == pytest.approx(
        0.0,
        abs=2.0,
    )

    assert result.indicated_alt_ft == pytest.approx(
        result.pressure_alt_ft,
        abs=2.0,
    )


def test_nonstandard_setting_changes_only_indicated_altitude() -> None:
    computer = FlightComputer()

    assert (
        computer.baro_setting_controller
        .set_setting(30.42)
        is True
    )

    result = computer.update(make_raw())

    assert result.pressure_alt_ft == pytest.approx(
        0.0,
        abs=2.0,
    )

    assert result.indicated_alt_ft > (
        result.pressure_alt_ft + 400.0
    )


def test_flight_computer_exposes_runtime_baro_controller() -> None:
    computer = FlightComputer()

    assert (
        computer.baro_setting_controller.setting_inhg
        == pytest.approx(
            computer.config.altitude.baro_setting_inhg
        )
    )


def test_runtime_baro_adjustment_changes_indicated_altitude_only() -> None:
    computer = FlightComputer()

    before = computer.update(
        make_raw()
    )

    for _ in range(50):
        computer.baro_setting_controller.increment()

    after = computer.update(
        make_raw()
    )

    assert after.pressure_alt_ft == pytest.approx(
        before.pressure_alt_ft,
        abs=0.01,
    )

    assert after.indicated_alt_ft > (
        before.indicated_alt_ft + 400.0
    )


def test_invalid_runtime_baro_does_not_corrupt_flight_altitude() -> None:
    computer = FlightComputer()

    before = computer.update(
        make_raw()
    )

    assert (
        computer.baro_setting_controller
        .set_setting(float("nan"))
        is False
    )

    after = computer.update(
        make_raw()
    )

    assert after.pressure_alt_ft == pytest.approx(
        before.pressure_alt_ft,
        abs=0.01,
    )

    assert after.indicated_alt_ft == pytest.approx(
        before.indicated_alt_ft,
        abs=0.01,
    )
