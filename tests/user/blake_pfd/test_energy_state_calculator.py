import pytest

from pyefis.user.blake_pfd.core.energy_state_calculator import (
    EnergyStateCalculator,
)


def test_calculates_valid_energy_state() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=5000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
    )

    assert state.valid is True
    assert state.altitude_above_terrain_ft == 4000.0
    assert state.potential_energy_height_ft == 4000.0
    assert state.kinetic_energy_height_ft > 0.0
    assert state.total_energy_height_ft > 4000.0
    assert state.trend == "STABLE"


def test_zero_airspeed_has_no_kinetic_energy() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=3000.0,
        terrain_elevation_ft=500.0,
        airspeed_kt=0.0,
    )

    assert state.kinetic_energy_height_ft == 0.0
    assert state.total_energy_height_ft == 2500.0


def test_energy_increasing_with_altitude() -> None:
    calculator = EnergyStateCalculator(
        stable_trend_threshold_fpm=50.0,
    )

    calculator.calculate(
        altitude_ft=4000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
        timestamp_s=10.0,
    )

    state = calculator.calculate(
        altitude_ft=4100.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
        timestamp_s=20.0,
    )

    assert state.energy_trend_fpm == pytest.approx(
        600.0
    )
    assert state.trend == "INCREASING"


def test_energy_decreasing_with_altitude() -> None:
    calculator = EnergyStateCalculator(
        stable_trend_threshold_fpm=50.0,
    )

    calculator.calculate(
        altitude_ft=4000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
        timestamp_s=10.0,
    )

    state = calculator.calculate(
        altitude_ft=3900.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
        timestamp_s=20.0,
    )

    assert state.energy_trend_fpm == pytest.approx(
        -600.0
    )
    assert state.trend == "DECREASING"


def test_airspeed_change_affects_energy_trend() -> None:
    calculator = EnergyStateCalculator(
        stable_trend_threshold_fpm=1.0,
    )

    first = calculator.calculate(
        altitude_ft=4000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=60.0,
        timestamp_s=10.0,
    )

    second = calculator.calculate(
        altitude_ft=4000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=90.0,
        timestamp_s=20.0,
    )

    assert (
        second.total_energy_height_ft
        > first.total_energy_height_ft
    )
    assert second.energy_trend_fpm > 0.0
    assert second.trend == "INCREASING"


def test_glide_margin_is_positive_when_site_reachable() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=5000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
        selected_site_distance_nm=6.0,
        glide_range_nm=10.0,
    )

    assert state.glide_margin_nm == 4.0


def test_glide_margin_is_negative_when_site_unreachable() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=5000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
        selected_site_distance_nm=12.0,
        glide_range_nm=10.0,
    )

    assert state.glide_margin_nm == -2.0


def test_climb_margin_compares_current_and_target_altitude() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=5000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
        target_altitude_ft=4500.0,
    )

    assert state.climb_margin_ft == 500.0


def test_invalid_required_input_returns_invalid_state() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=None,
        terrain_elevation_ft=1000.0,
        airspeed_kt=80.0,
    )

    assert state.valid is False


def test_negative_airspeed_returns_invalid_state() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=5000.0,
        terrain_elevation_ft=1000.0,
        airspeed_kt=-1.0,
    )

    assert state.valid is False


def test_nonadvancing_timestamp_does_not_create_trend() -> None:
    calculator = EnergyStateCalculator()

    calculator.calculate(
        altitude_ft=4000.0,
        airspeed_kt=80.0,
        timestamp_s=10.0,
    )

    state = calculator.calculate(
        altitude_ft=4200.0,
        airspeed_kt=80.0,
        timestamp_s=10.0,
    )

    assert state.energy_trend_fpm == 0.0
    assert state.trend == "STABLE"


def test_reset_clears_previous_sample() -> None:
    calculator = EnergyStateCalculator()

    calculator.calculate(
        altitude_ft=4000.0,
        airspeed_kt=80.0,
        timestamp_s=10.0,
    )

    calculator.reset()

    state = calculator.calculate(
        altitude_ft=4500.0,
        airspeed_kt=80.0,
        timestamp_s=20.0,
    )

    assert state.energy_trend_fpm == 0.0


def test_constructor_rejects_negative_threshold() -> None:
    with pytest.raises(ValueError):
        EnergyStateCalculator(
            stable_trend_threshold_fpm=-1.0,
        )