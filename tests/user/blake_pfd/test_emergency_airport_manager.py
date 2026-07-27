from pyefis.user.blake_pfd.core.emergency_airport_manager import (
    EmergencyAirportManager,
)
from pyefis.user.blake_pfd.core.glide_calculator import (
    GlideCalculator,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    NearbyAirportRecord,
    ReachableAirportPipeline,
)


def airport(
    identifier: str,
    distance_nm: float,
    bearing_deg: float = 0.0,
    elevation_ft: float = 500.0,
) -> NearbyAirportRecord:
    return NearbyAirportRecord(
        identifier=identifier,
        distance_nm=distance_nm,
        bearing_deg=bearing_deg,
        elevation_ft=elevation_ft,
    )


def manager_with_test_glide() -> EmergencyAirportManager:
    pipeline = ReachableAirportPipeline(
        glide_calculator=GlideCalculator(
            glide_ratio=9.0,
            best_glide_speed_kt=80.0,
            reserve_altitude_ft=0.0,
        )
    )

    return EmergencyAirportManager(
        pipeline=pipeline,
    )


def test_inactive_emergency_still_updates_reachability() -> None:
    manager = manager_with_test_glide()

    state = manager.update(
        airports=[
            airport(
                "KHAO",
                distance_nm=4.0,
            )
        ],
        aircraft_altitude_ft=6000.0,
        emergency_active=False,
    )

    assert state.result.valid is True
    assert len(state.result.ranked) == 1
    assert state.advice.severity == "NORMAL"
    assert state.advice.airport_identifier is None


def test_active_emergency_selects_best_airport() -> None:
    manager = manager_with_test_glide()

    state = manager.update(
        airports=[
            airport(
                "KHAO",
                distance_nm=4.0,
            ),
            airport(
                "KDAY",
                distance_nm=20.0,
            ),
        ],
        aircraft_altitude_ft=6000.0,
        emergency_active=True,
    )

    assert state.result.valid is True
    assert state.advice.airport_identifier == "KHAO"
    assert state.advice.title == "Best Airport: KHAO"


def test_directional_wind_changes_best_airport() -> None:
    manager = manager_with_test_glide()

    state = manager.update(
        airports=[
            airport(
                "NORTH",
                distance_nm=6.0,
                bearing_deg=0.0,
            ),
            airport(
                "SOUTH",
                distance_nm=6.0,
                bearing_deg=180.0,
            ),
        ],
        aircraft_altitude_ft=5000.0,
        wind_speed_kt=30.0,
        wind_from_deg=0.0,
        emergency_active=True,
    )

    assert state.advice.airport_identifier == "SOUTH"


def test_no_reachable_airport_creates_critical_advice() -> None:
    manager = manager_with_test_glide()

    state = manager.update(
        airports=[
            airport(
                "FAR",
                distance_nm=50.0,
            )
        ],
        aircraft_altitude_ft=3000.0,
        emergency_active=True,
    )

    assert state.result.ranked == ()
    assert state.advice.severity == "CRITICAL"
    assert state.advice.title == "No Reachable Airport"


def test_invalid_altitude_creates_unavailable_advice() -> None:
    manager = manager_with_test_glide()

    state = manager.update(
        airports=[
            airport(
                "TEST",
                distance_nm=3.0,
            )
        ],
        aircraft_altitude_ft=float("nan"),
        emergency_active=True,
    )

    assert state.result.valid is False
    assert state.advice.severity == "WARNING"
    assert state.advice.title == (
        "Diversion Data Unavailable"
    )


def test_clear_resets_manager_state() -> None:
    manager = manager_with_test_glide()

    manager.update(
        airports=[
            airport(
                "KHAO",
                distance_nm=3.0,
            )
        ],
        aircraft_altitude_ft=6000.0,
        emergency_active=True,
    )

    manager.clear()

    assert manager.state.result.valid is False
    assert manager.state.result.ranked == ()
    assert manager.state.advice.airport_identifier is None