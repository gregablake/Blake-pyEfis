import pytest

from pyefis.user.blake_pfd.core.wind_calculator import (
    WindCalculator,
)


def test_direct_headwind() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=20.0,
        wind_from_deg=360.0,
        course_deg=0.0,
    )

    assert result.valid is True
    assert result.headwind_kt == pytest.approx(
        20.0
    )
    assert result.tailwind_kt == 0.0
    assert result.crosswind_kt == pytest.approx(
        0.0,
        abs=0.001,
    )
    assert result.crosswind_direction == "NONE"


def test_direct_tailwind() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=15.0,
        wind_from_deg=180.0,
        course_deg=0.0,
    )

    assert result.headwind_kt == 0.0
    assert result.tailwind_kt == pytest.approx(
        15.0
    )
    assert result.crosswind_kt == pytest.approx(
        0.0,
        abs=0.001,
    )


def test_crosswind_from_right() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=12.0,
        wind_from_deg=90.0,
        course_deg=0.0,
    )

    assert result.headwind_kt == pytest.approx(
        0.0,
        abs=0.001,
    )
    assert result.crosswind_kt == pytest.approx(
        12.0
    )
    assert result.crosswind_direction == "RIGHT"


def test_crosswind_from_left() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=12.0,
        wind_from_deg=270.0,
        course_deg=0.0,
    )

    assert result.crosswind_kt == pytest.approx(
        12.0
    )
    assert result.crosswind_direction == "LEFT"


def test_quartering_headwind() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=20.0,
        wind_from_deg=45.0,
        course_deg=0.0,
    )

    assert result.headwind_kt == pytest.approx(
        14.142,
        rel=1e-3,
    )

    assert result.crosswind_kt == pytest.approx(
        14.142,
        rel=1e-3,
    )

    assert result.crosswind_direction == "RIGHT"


def test_angles_are_normalized() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=10.0,
        wind_from_deg=450.0,
        course_deg=360.0,
    )

    assert result.wind_from_deg == 90.0
    assert result.crosswind_direction == "RIGHT"


def test_invalid_input_returns_invalid_result() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=float("nan"),
        wind_from_deg=90.0,
        course_deg=0.0,
    )

    assert result.valid is False
    assert result.headwind_kt == 0.0
    assert result.crosswind_kt == 0.0


def test_negative_wind_speed_is_clamped() -> None:
    calculator = WindCalculator()

    result = calculator.calculate_components(
        wind_speed_kt=-10.0,
        wind_from_deg=90.0,
        course_deg=0.0,
    )

    assert result.valid is True
    assert result.wind_speed_kt == 0.0
    assert result.crosswind_kt == 0.0