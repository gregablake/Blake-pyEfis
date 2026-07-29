from types import SimpleNamespace

from pyefis.user.blake_pfd.core.emergency_detection import (
    EmergencyDetection,
)
from pyefis.user.blake_pfd.core.emergency_airport_manager import (
    EmergencyAirportManager,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    NearbyAirportRecord,
)


def test_detected_engine_failure_activates_airport_advice() -> None:
    detector = EmergencyDetection()
    manager = EmergencyAirportManager()

    emergency = detector.evaluate(
        engine_state=SimpleNamespace(
            running=False,
        ),
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
    )

    state = manager.update(
        airports=[
            NearbyAirportRecord(
                identifier="KHAO",
                distance_nm=3.0,
                bearing_deg=90.0,
                elevation_ft=600.0,
            )
        ],
        aircraft_altitude_ft=6000.0,
        wind_speed_kt=0.0,
        wind_from_deg=0.0,
        emergency_active=emergency.active,
    )

    assert emergency.active is True
    assert state.advice.airport_identifier == "KHAO"


def test_running_engine_keeps_airport_advice_inactive() -> None:
    detector = EmergencyDetection()
    manager = EmergencyAirportManager()

    emergency = detector.evaluate(
        engine_state=SimpleNamespace(
            running=True,
        ),
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
    )

    state = manager.update(
        airports=[
            NearbyAirportRecord(
                identifier="KHAO",
                distance_nm=3.0,
                bearing_deg=90.0,
                elevation_ft=600.0,
            )
        ],
        aircraft_altitude_ft=6000.0,
        emergency_active=emergency.active,
    )

    assert emergency.active is False
    assert state.advice.severity == "NORMAL"
    assert state.advice.airport_identifier is None
    
def test_pilot_selected_emergency_activates_airport_advice() -> None:
    detector = EmergencyDetection()
    manager = EmergencyAirportManager()

    emergency = detector.evaluate(
        engine_state=SimpleNamespace(
            running=True,
        ),
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
        pilot_selected=True,
    )

    state = manager.update(
        airports=[
            NearbyAirportRecord(
                identifier="KHAO",
                distance_nm=3.0,
                bearing_deg=90.0,
                elevation_ft=600.0,
            )
        ],
        aircraft_altitude_ft=6000.0,
        emergency_active=emergency.active,
    )

    assert emergency.active is True
    assert emergency.reason == "PILOT_SELECTED"
    assert state.advice.airport_identifier == "KHAO"