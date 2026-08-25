from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.core.emergency_detection import (
    EmergencyDetection,
)


def test_zero_rpm_in_cruise_detects_engine_stopped() -> None:
    detector = EmergencyDetection()

    engine_state = SimpleNamespace(
        data=SimpleNamespace(
            rpm=0.0,
        ),
    )

    flight_state = SimpleNamespace(
        phase="CRUISE",
    )

    status = detector.evaluate(
        engine_state=engine_state,
        flight_state=flight_state,
    )

    assert status.active is True
    assert status.automatic is True
    assert status.reason == "ENGINE_STOPPED"
    
def test_invalid_rpm_does_not_false_trigger_engine_stopped() -> None:
    detector = EmergencyDetection()

    engine_state = SimpleNamespace(
        data=SimpleNamespace(
            rpm=0.0,
        ),
    )

    flight_state = SimpleNamespace(
        phase="CRUISE",
    )

    sensor_status = SimpleNamespace(
        rpm=SimpleNamespace(
            valid=False,
            fresh=False,
        ),
    )

    status = detector.evaluate(
        engine_state=engine_state,
        flight_state=flight_state,
        sensor_status=sensor_status,
    )

    assert status.active is False
    assert status.reason == ""