import pytest

from pyefis.user.blake_pfd.core.terrain_awareness import (
    TerrainAwareness,
    TerrainProfilePoint,
)


def test_level_flight_with_safe_clearance() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=5000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=100.0,
        profile=[
            TerrainProfilePoint(
                distance_nm=2.0,
                elevation_ft=1000.0,
            ),
            TerrainProfilePoint(
                distance_nm=5.0,
                elevation_ft=2000.0,
            ),
        ],
    )

    assert state.valid is True
    assert state.highest_terrain_ft == 2000.0
    assert state.minimum_clearance_ft == 3000.0
    assert state.limiting_distance_nm == 5.0
    assert state.warning_level == "NONE"


def test_descent_reduces_future_clearance() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=5000.0,
        vertical_speed_fpm=-1000.0,
        ground_speed_kt=120.0,
        profile=[
            TerrainProfilePoint(
                distance_nm=6.0,
                elevation_ft=3000.0,
            ),
        ],
    )

    assert state.valid is True
    assert state.projected_altitude_ft == pytest.approx(
        2000.0
    )
    assert state.minimum_clearance_ft == pytest.approx(
        -1000.0
    )
    assert state.warning_level == "CRITICAL"
    assert state.message == "PULL UP"


def test_climb_improves_future_clearance() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=3000.0,
        vertical_speed_fpm=500.0,
        ground_speed_kt=100.0,
        profile=[
            TerrainProfilePoint(
                distance_nm=10.0,
                elevation_ft=2500.0,
            ),
        ],
    )

    assert state.projected_altitude_ft == pytest.approx(
        6000.0
    )
    assert state.minimum_clearance_ft == pytest.approx(
        3500.0
    )
    assert state.warning_level == "NONE"


def test_low_clearance_creates_caution() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=3000.0,
        ground_speed_kt=100.0,
        profile=[
            TerrainProfilePoint(
                distance_nm=2.0,
                elevation_ft=2200.0,
            ),
        ],
    )

    assert state.minimum_clearance_ft == 800.0
    assert state.warning_level == "CAUTION"
    assert state.message == "TERRAIN CLEARANCE LOW"


def test_warning_clearance_creates_warning() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=3000.0,
        ground_speed_kt=100.0,
        profile=[
            TerrainProfilePoint(
                distance_nm=2.0,
                elevation_ft=2600.0,
            ),
        ],
    )

    assert state.minimum_clearance_ft == 400.0
    assert state.warning_level == "WARNING"
    assert state.message == "TERRAIN AHEAD"


def test_empty_profile_returns_invalid_state() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=3000.0,
        ground_speed_kt=100.0,
        profile=[],
    )

    assert state.valid is False
    assert state.message == "TERRAIN DATA UNAVAILABLE"


def test_invalid_profile_point_returns_invalid_state() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=3000.0,
        ground_speed_kt=100.0,
        profile=[
            TerrainProfilePoint(
                distance_nm=-1.0,
                elevation_ft=1000.0,
            ),
        ],
    )

    assert state.valid is False
    assert state.message == "TERRAIN DATA INVALID"


def test_zero_ground_speed_uses_current_altitude() -> None:
    awareness = TerrainAwareness()

    state = awareness.evaluate(
        aircraft_altitude_ft=3000.0,
        vertical_speed_fpm=-1000.0,
        ground_speed_kt=0.0,
        profile=[
            TerrainProfilePoint(
                distance_nm=3.0,
                elevation_ft=1000.0,
            ),
        ],
    )

    assert state.projected_altitude_ft == 3000.0
    assert state.minimum_clearance_ft == 2000.0


def test_constructor_rejects_bad_threshold_order() -> None:
    with pytest.raises(ValueError):
        TerrainAwareness(
            caution_clearance_ft=400.0,
            warning_clearance_ft=500.0,
            critical_clearance_ft=100.0,
        )


def test_constructor_rejects_negative_threshold() -> None:
    with pytest.raises(ValueError):
        TerrainAwareness(
            critical_clearance_ft=-1.0,
        )