import pytest

from pyefis.user.blake_pfd.core.fuel_state_calculator import (
    FuelStateCalculator,
)


def test_calculates_endurance_and_range() -> None:
    calculator = FuelStateCalculator()

    result = calculator.calculate(
        remaining_gal=16.0,
        used_gal=8.0,
        flow_gph=8.0,
        ground_speed_kt=110.0,
    )

    assert result.endurance_hr == 2.0
    assert result.range_nm == 220.0
    assert result.calculation_valid is True


def test_low_ground_speed_keeps_endurance_but_uses_range_fallback() -> None:
    calculator = FuelStateCalculator()

    result = calculator.calculate(
        remaining_gal=16.0,
        used_gal=8.0,
        flow_gph=8.0,
        ground_speed_kt=10.0,
        fallback_range_nm=180.0,
    )

    assert result.endurance_hr == 2.0
    assert result.range_nm == 180.0
    assert result.calculation_valid is True


def test_low_flow_uses_fallback_values() -> None:
    calculator = FuelStateCalculator()

    result = calculator.calculate(
        remaining_gal=16.0,
        used_gal=8.0,
        flow_gph=0.0,
        ground_speed_kt=110.0,
        fallback_endurance_hr=1.8,
        fallback_range_nm=190.0,
    )

    assert result.endurance_hr == 1.8
    assert result.range_nm == 190.0
    assert result.calculation_valid is False


def test_nonfinite_values_are_sanitized() -> None:
    calculator = FuelStateCalculator()

    result = calculator.calculate(
        remaining_gal=float("nan"),
        used_gal=float("inf"),
        flow_gph=8.0,
        ground_speed_kt=100.0,
    )

    assert result.remaining_gal == 0.0
    assert result.used_gal == 0.0
    assert result.endurance_hr == 0.0
    assert result.range_nm == 0.0


def test_invalid_configuration_raises() -> None:
    with pytest.raises(
        ValueError,
        match="minimum_flow_gph",
    ):
        FuelStateCalculator(
            minimum_flow_gph=0.0,
        )

    with pytest.raises(
        ValueError,
        match="minimum_ground_speed_kt",
    ):
        FuelStateCalculator(
            minimum_ground_speed_kt=float("nan"),
        )