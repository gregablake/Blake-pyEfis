from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_alert_gate import (
    TerrainAlertGate,
)


def startup_status(
    *,
    enabled: bool,
    message: str = "",
):
    return SimpleNamespace(
        predictive_alerts_enabled=enabled,
        message=message,
    )


def awareness_state(
    *,
    manager_valid: bool = True,
    awareness_valid: bool = True,
    warning_level: str = "NONE",
    message: str = "",
    minimum_clearance_ft: float = 2000.0,
):
    return SimpleNamespace(
        valid=manager_valid,
        message=message,
        awareness=SimpleNamespace(
            valid=awareness_valid,
            warning_level=warning_level,
            message=message,
            minimum_clearance_ft=(
                minimum_clearance_ft
            ),
        ),
    )


def test_fallback_terrain_suppresses_alerts() -> None:
    gate = TerrainAlertGate()

    result = gate.evaluate(
        startup_status=startup_status(
            enabled=False,
        ),
        terrain_awareness_state=awareness_state(
            warning_level="CRITICAL",
            message="PULL UP",
            minimum_clearance_ft=-100.0,
        ),
        real_terrain_enabled=False,
    )

    assert result.active is False
    assert (
        result.predictive_alerts_enabled
        is False
    )
    assert (
        result.suppressed_reason
        == "REAL TERRAIN DATA NOT ENABLED"
    )


def test_startup_validation_can_disable_alerts() -> None:
    gate = TerrainAlertGate()

    result = gate.evaluate(
        startup_status=startup_status(
            enabled=False,
            message="SRTM TILE N39W085 MISSING",
        ),
        terrain_awareness_state=awareness_state(
            warning_level="CRITICAL",
            message="PULL UP",
        ),
        real_terrain_enabled=True,
    )

    assert result.active is False
    assert (
        result.suppressed_reason
        == "SRTM TILE N39W085 MISSING"
    )


def test_invalid_manager_state_suppresses_alert() -> None:
    gate = TerrainAlertGate()

    result = gate.evaluate(
        startup_status=startup_status(
            enabled=True,
        ),
        terrain_awareness_state=awareness_state(
            manager_valid=False,
            message="TERRAIN SAMPLE UNAVAILABLE",
        ),
        real_terrain_enabled=True,
    )

    assert result.active is False
    assert (
        result.suppressed_reason
        == "TERRAIN SAMPLE UNAVAILABLE"
    )


def test_none_warning_does_not_activate() -> None:
    gate = TerrainAlertGate()

    result = gate.evaluate(
        startup_status=startup_status(
            enabled=True,
        ),
        terrain_awareness_state=awareness_state(
            warning_level="NONE",
            minimum_clearance_ft=3000.0,
        ),
        real_terrain_enabled=True,
    )

    assert result.active is False
    assert result.warning_level == "NONE"
    assert (
        result.predictive_alerts_enabled
        is True
    )
    assert result.minimum_clearance_ft == 3000.0


def test_caution_alert_is_allowed() -> None:
    gate = TerrainAlertGate()

    result = gate.evaluate(
        startup_status=startup_status(
            enabled=True,
        ),
        terrain_awareness_state=awareness_state(
            warning_level="CAUTION",
            message="TERRAIN CLEARANCE LOW",
            minimum_clearance_ft=800.0,
        ),
        real_terrain_enabled=True,
    )

    assert result.active is True
    assert result.warning_level == "CAUTION"
    assert (
        result.message
        == "TERRAIN CLEARANCE LOW"
    )
    assert result.minimum_clearance_ft == 800.0


def test_warning_alert_is_allowed() -> None:
    gate = TerrainAlertGate()

    result = gate.evaluate(
        startup_status=startup_status(
            enabled=True,
        ),
        terrain_awareness_state=awareness_state(
            warning_level="WARNING",
            message="TERRAIN AHEAD",
            minimum_clearance_ft=400.0,
        ),
        real_terrain_enabled=True,
    )

    assert result.active is True
    assert result.warning_level == "WARNING"
    assert result.message == "TERRAIN AHEAD"


def test_critical_alert_is_allowed() -> None:
    gate = TerrainAlertGate()

    result = gate.evaluate(
        startup_status=startup_status(
            enabled=True,
        ),
        terrain_awareness_state=awareness_state(
            warning_level="CRITICAL",
            message="PULL UP",
            minimum_clearance_ft=-50.0,
        ),
        real_terrain_enabled=True,
    )

    assert result.active is True
    assert result.warning_level == "CRITICAL"
    assert result.message == "PULL UP"
    assert result.minimum_clearance_ft == -50.0