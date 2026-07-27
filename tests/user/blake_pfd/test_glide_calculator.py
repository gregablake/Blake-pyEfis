import pytest

from pyefis.user.blake_pfd.core.glide_calculator import (
    FEET_PER_NAUTICAL_MILE,
    GlideCalculator,
)


def test_calculates_still_air_glide_range() -> None:
    calculator = GlideCalculator(
        glide_ratio=9.0,
        best_glide_speed_kt=80.0,
        reserve_altitude_ft=1000.0,
    )

    result = calculator.calculate(
        altitude_ft=5000.0,
        terrain_elevation_ft=1000.0,
    )

    expected_altitude = 3000.0

    assert result.valid is True
    assert result.altitude_available_ft == 3000.0

    assert result.still_air_range_nm == pytest.approx(
        expected_altitude
        * 9.0
        / FEET_PER_NAUTICAL_MILE
    )

    assert result.wind_corrected_range_nm == pytest.approx(
        result.still_air_range_nm
    )


def test_headwind_reduces_glide_range() -> None:
    calculator = GlideCalculator(
        glide_ratio=9.0,
        best_glide_speed_kt=80.0,
        reserve_altitude_ft=0.0,
    )

    result = calculator.calculate(
        altitude_ft=5000.0,
        headwind_kt=20.0,
    )

    assert result.valid is True
    assert result.ground_speed_kt == 60.0

    assert (
        result.wind_corrected_range_nm
        < result.still_air_range_nm
    )


def test_tailwind_increases_glide_range() -> None:
    calculator = GlideCalculator(
        glide_ratio=9.0,
        best_glide_speed_kt=80.0,
        reserve_altitude_ft=0.0,
    )

    result = calculator.calculate(
        altitude_ft=5000.0,
        tailwind_kt=20.0,
    )

    assert result.ground_speed_kt == 100.0

    assert (
        result.wind_corrected_range_nm
        > result.still_air_range_nm
    )


def test_no_altitude_above_reserve_returns_zero_range() -> None:
    calculator = GlideCalculator(
        reserve_altitude_ft=1000.0,
    )

    result = calculator.calculate(
        altitude_ft=1500.0,
        terrain_elevation_ft=500.0,
    )

    assert result.valid is True
    assert result.altitude_available_ft == 0.0
    assert result.still_air_range_nm == 0.0
    assert result.wind_corrected_range_nm == 0.0


def test_ground_speed_is_clamped_for_extreme_headwind() -> None:
    calculator = GlideCalculator(
        best_glide_speed_kt=80.0,
        minimum_ground_speed_kt=20.0,
        reserve_altitude_ft=0.0,
    )

    result = calculator.calculate(
        altitude_ft=5000.0,
        headwind_kt=100.0,
    )

    assert result.ground_speed_kt == 20.0
    assert result.wind_corrected_range_nm > 0.0


def test_invalid_runtime_input_returns_invalid_result() -> None:
    calculator = GlideCalculator()

    result = calculator.calculate(
        altitude_ft=float("nan"),
    )

    assert result.valid is False
    assert result.wind_corrected_range_nm == 0.0


def test_invalid_configuration_raises() -> None:
    with pytest.raises(
        ValueError,
        match="glide_ratio",
    ):
        GlideCalculator(
            glide_ratio=0.0,
        )

    with pytest.raises(
        ValueError,
        match="best_glide_speed_kt",
    ):
        GlideCalculator(
            best_glide_speed_kt=float("nan"),
        )

    with pytest.raises(
        ValueError,
        match="reserve_altitude_ft",
    ):
        GlideCalculator(
            reserve_altitude_ft=-1.0,
        )