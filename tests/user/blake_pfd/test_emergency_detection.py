from types import SimpleNamespace

from pyefis.user.blake_pfd.core.emergency_detection import (
    EmergencyDetection,
)


def test_engine_running_not_emergency():
    detector = EmergencyDetection()

    result = detector.evaluate(
        engine_state=SimpleNamespace(
            running=True,
        ),
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
    )

    assert result.active is False


def test_engine_failure_in_cruise():
    detector = EmergencyDetection()

    result = detector.evaluate(
        engine_state=SimpleNamespace(
            running=False,
        ),
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
    )

    assert result.active is True
    assert result.reason == "ENGINE_STOPPED"


def test_engine_failure_on_ground():
    detector = EmergencyDetection()

    result = detector.evaluate(
        engine_state=SimpleNamespace(
            running=False,
        ),
        flight_state=SimpleNamespace(
            phase="PARKED",
        ),
    )

    assert result.active is False


def test_missing_engine_state():
    detector = EmergencyDetection()

    result = detector.evaluate(
        engine_state=None,
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
    )

    assert result.active is False