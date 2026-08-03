from pyefis.user.blake_pfd.core.energy_state_calculator import (
    EnergyStateCalculator,
)


def test_live_energy_inputs_create_valid_state() -> None:
    calculator = EnergyStateCalculator()

    state = calculator.calculate(
        altitude_ft=5000.0,
        terrain_elevation_ft=800.0,
        airspeed_kt=80.0,
        timestamp_s=10.0,
        selected_site_distance_nm=6.0,
        glide_range_nm=10.0,
    )

    assert state.valid is True
    assert state.altitude_above_terrain_ft == 4200.0
    assert state.glide_margin_nm == 4.0


def test_runtime_samples_generate_energy_trend() -> None:
    calculator = EnergyStateCalculator(
        stable_trend_threshold_fpm=50.0,
    )

    calculator.calculate(
        altitude_ft=4000.0,
        terrain_elevation_ft=500.0,
        airspeed_kt=80.0,
        timestamp_s=10.0,
    )

    state = calculator.calculate(
        altitude_ft=4100.0,
        terrain_elevation_ft=500.0,
        airspeed_kt=80.0,
        timestamp_s=20.0,
    )

    assert state.valid is True
    assert state.energy_trend_fpm > 0.0
    assert state.trend == "INCREASING"