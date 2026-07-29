from types import SimpleNamespace

from pyefis.user.blake_pfd.core.emergency_detection import (
    EmergencyDetection,
)


def test_engine_running_not_emergency() -> None:
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
    assert result.reason == ""
    assert result.automatic is False
    assert result.pilot_selected is False


def test_engine_failure_in_cruise() -> None:
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
    assert result.automatic is True
    assert result.pilot_selected is False


def test_engine_failure_on_ground() -> None:
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


def test_missing_engine_state() -> None:
    detector = EmergencyDetection()

    result = detector.evaluate(
        engine_state=None,
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
    )

    assert result.active is False


def test_pilot_can_activate_emergency() -> None:
    detector = EmergencyDetection()

    result = detector.evaluate(
        engine_state=SimpleNamespace(
            running=True,
        ),
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
        pilot_selected=True,
    )

    assert result.active is True
    assert result.reason == "PILOT_SELECTED"
    assert result.automatic is False
    assert result.pilot_selected is True


def test_pilot_override_works_without_engine_state() -> None:
    detector = EmergencyDetection()

    result = detector.evaluate(
        engine_state=None,
        flight_state=None,
        pilot_selected=True,
    )

    assert result.active is True
    assert result.reason == "PILOT_SELECTED"