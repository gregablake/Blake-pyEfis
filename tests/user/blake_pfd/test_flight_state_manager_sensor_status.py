from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.core.flight_state_manager import (
    FlightPhase,
    FlightStateManager,
)


def test_invalid_rpm_does_not_create_false_landing_roll() -> None:
    manager = FlightStateManager()

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    invalid = EngineChannelStatus(
        valid=False,
        fresh=False,
        message="IMPLAUSIBLE DATA",
    )

    pfd = SimpleNamespace(
        ground_speed_kt=20.0,
        pressure_alt_ft=0.0,
        vsi_fpm=0.0,
    )

    engine = SimpleNamespace(
        rpm=0.0,
    )

    status = EngineSensorStatus(
        rpm=invalid,
        volts=healthy,
        oil_pressure=healthy,
        oil_temperature=healthy,
        cht=(
            healthy,
            healthy,
            healthy,
            healthy,
            healthy,
            healthy,
        ),
        egt=(
            healthy,
            healthy,
        ),
    )

    state = manager.update(
        pfd,
        engine,
        sensor_status=status,
    )

    assert state.landing_roll is False
    assert state.takeoff_roll is False
    assert state.phase == FlightPhase.TAXI.value