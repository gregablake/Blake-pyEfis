from __future__ import annotations

from pyefis.user.blake_pfd.core.engine_manager import (
    EngineManager,
)
from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_invalid_hot_cht_does_not_reduce_engine_health() -> None:
    manager = EngineManager()

    engine = EngineData(
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[
            350.0,
            355.0,
            700.0,
            352.0,
            354.0,
            351.0,
        ],
        egt_f=[
            1350.0,
            1360.0,
        ],
        alternator_online=True,
    )

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

    status = EngineSensorStatus(
        oil_pressure=healthy,
        oil_temperature=healthy,
        cht=(
            healthy,
            healthy,
            invalid,
            healthy,
            healthy,
            healthy,
        ),
        egt=(
            healthy,
            healthy,
        ),
    )

    result = manager.update(
        engine,
        sensor_status=status,
    )

    assert result.status == "NORMAL"
    assert result.health_score == 100
    assert result.cht_max_f == 355.0
def test_invalid_electrical_status_does_not_reduce_engine_health() -> None:
    manager = EngineManager()

    engine = EngineData(
        volts=0.0,
        amps=0.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[350.0] * 6,
        egt_f=[1350.0, 1360.0],
        alternator_online=False,
    )

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

    status = EngineSensorStatus(
        volts=invalid,
        amps=invalid,
        oil_pressure=healthy,
        oil_temperature=healthy,
        cht=(healthy,) * 6,
        egt=(healthy,) * 2,
    )

    result = manager.update(
        engine,
        sensor_status=status,
    )

    assert result.status == "NORMAL"
    assert result.health_score == 100


def test_valid_electrical_status_still_reduces_health_for_alternator_failure() -> None:
    manager = EngineManager()

    engine = EngineData(
        volts=14.2,
        amps=5.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[350.0] * 6,
        egt_f=[1350.0, 1360.0],
        alternator_online=False,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    status = EngineSensorStatus(
        volts=healthy,
        amps=healthy,
        oil_pressure=healthy,
        oil_temperature=healthy,
        cht=(healthy,) * 6,
        egt=(healthy,) * 2,
    )

    result = manager.update(
        engine,
        sensor_status=status,
    )

    assert result.status == "CAUTION"
    assert result.health_score == 85
