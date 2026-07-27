import pytest

from pyefis.user.blake_pfd.core.airport_glide_analyzer import (
    AirportGlideAnalyzer,
)
from pyefis.user.blake_pfd.core.glide_calculator import (
    GlideCalculator,
)


def test_reachable_airport_has_positive_margin() -> None:
    glide = GlideCalculator(
        glide_ratio=9.0,
        best_glide_speed_kt=80.0,
        reserve_altitude_ft=1000.0,
    ).calculate(
        altitude_ft=6000.0,
        terrain_elevation_ft=1000.0,
    )

    analyzer = AirportGlideAnalyzer()

    result = analyzer.analyze(
        identifier="KHAO",
        distance_nm=4.0,
        bearing_deg=90.0,
        airport_elevation_ft=633.0,
        aircraft_altitude_ft=6000.0,
        glide=glide,
    )

    assert result.valid is True
    assert result.reachable is True
    assert result.identifier == "KHAO"
    assert result.safety_margin_ft > 0.0
    assert result.arrival_altitude_ft > 633.0


def test_airport_beyond_glide_range_is_not_reachable() -> None:
    glide = GlideCalculator(
        glide_ratio=9.0,
        best_glide_speed_kt=80.0,
        reserve_altitude_ft=1000.0,
    ).calculate(
        altitude_ft=4000.0,
        terrain_elevation_ft=1000.0,
    )

    analyzer = AirportGlideAnalyzer()

    result = analyzer.analyze(
        identifier="KDAY",
        distance_nm=20.0,
        bearing_deg=30.0,
        airport_elevation_ft=1009.0,
        aircraft_altitude_ft=4000.0,
        glide=glide,
    )

    assert result.valid is True
    assert result.reachable is False
    assert result.safety_margin_ft < 0.0


def test_headwind_can_make_airport_unreachable() -> None:
    calculator = GlideCalculator(
        glide_ratio=9.0,
        best_glide_speed_kt=80.0,
        reserve_altitude_ft=0.0,
    )

    still_air = calculator.calculate(
        altitude_ft=5000.0,
    )

    headwind = calculator.calculate(
        altitude_ft=5000.0,
        headwind_kt=35.0,
    )

    analyzer = AirportGlideAnalyzer()

    still_air_result = analyzer.analyze(
        identifier="TEST",
        distance_nm=6.0,
        bearing_deg=0.0,
        airport_elevation_ft=0.0,
        aircraft_altitude_ft=5000.0,
        glide=still_air,
    )

    headwind_result = analyzer.analyze(
        identifier="TEST",
        distance_nm=6.0,
        bearing_deg=0.0,
        airport_elevation_ft=0.0,
        aircraft_altitude_ft=5000.0,
        glide=headwind,
    )

    assert still_air_result.reachable is True
    assert headwind_result.reachable is False


def test_zero_distance_airport_is_reachable() -> None:
    glide = GlideCalculator().calculate(
        altitude_ft=3000.0,
    )

    analyzer = AirportGlideAnalyzer()

    result = analyzer.analyze(
        identifier="HERE",
        distance_nm=0.0,
        bearing_deg=450.0,
        airport_elevation_ft=500.0,
        aircraft_altitude_ft=3000.0,
        glide=glide,
    )

    assert result.valid is True
    assert result.reachable is True
    assert result.bearing_deg == 90.0
    assert result.arrival_altitude_ft == 3000.0
    assert result.safety_margin_ft == 2500.0


def test_required_glide_ratio_is_reported() -> None:
    glide = GlideCalculator(
        glide_ratio=10.0,
        reserve_altitude_ft=0.0,
    ).calculate(
        altitude_ft=6000.0,
    )

    analyzer = AirportGlideAnalyzer()

    result = analyzer.analyze(
        identifier="TEST",
        distance_nm=5.0,
        bearing_deg=180.0,
        airport_elevation_ft=1000.0,
        aircraft_altitude_ft=6000.0,
        glide=glide,
    )

    expected = (
        5.0 * 6076.12
    ) / 5000.0

    assert result.required_glide_ratio == pytest.approx(
        expected
    )


def test_invalid_glide_returns_invalid_candidate() -> None:
    invalid_glide = GlideCalculator().calculate(
        altitude_ft=float("nan"),
    )

    analyzer = AirportGlideAnalyzer()

    result = analyzer.analyze(
        identifier="TEST",
        distance_nm=5.0,
        bearing_deg=90.0,
        airport_elevation_ft=500.0,
        aircraft_altitude_ft=5000.0,
        glide=invalid_glide,
    )

    assert result.valid is False
    assert result.reachable is False


def test_invalid_airport_input_returns_invalid_candidate() -> None:
    glide = GlideCalculator().calculate(
        altitude_ft=5000.0,
    )

    analyzer = AirportGlideAnalyzer()

    result = analyzer.analyze(
        identifier="TEST",
        distance_nm=float("nan"),
        bearing_deg=90.0,
        airport_elevation_ft=500.0,
        aircraft_altitude_ft=5000.0,
        glide=glide,
    )

    assert result.valid is False