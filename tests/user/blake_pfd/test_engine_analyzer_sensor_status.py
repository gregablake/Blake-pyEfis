from __future__ import annotations

from pyefis.user.blake_pfd.core.engine_analyzer import (
    EngineAnalyzer,
)
from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_invalid_hot_cht_does_not_create_critical_analysis() -> None:
    analyzer = EngineAnalyzer()

    engine = EngineData(
        rpm=2450.0,
        volts=14.2,
        amps=5.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        fuel_pressure_psi=4.5,
        fuel_flow_gph=7.0,
        cht_f=[
            350.0,
            350.0,
            700.0,
            350.0,
            350.0,
            350.0,
        ],
        egt_f=[
            1350.0,
            1350.0,
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
        rpm=healthy,
        volts=healthy,
        amps=healthy,
        oil_pressure=healthy,
        oil_temperature=healthy,
        fuel_pressure=healthy,
        fuel_flow=healthy,
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

    result = analyzer.analyze(
        engine,
        sensor_status=status,
    )

    assert result.severity == "NORMAL"
    assert result.hottest_cht_f == 350.0
    
def test_valid_hot_cht_still_creates_critical_analysis() -> None:
    analyzer = EngineAnalyzer()

    engine = EngineData(
        rpm=2450.0,
        volts=14.2,
        amps=5.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        fuel_pressure_psi=4.5,
        fuel_flow_gph=7.0,
        cht_f=[
            350.0,
            350.0,
            460.0,
            350.0,
            350.0,
            350.0,
        ],
        egt_f=[
            1350.0,
            1350.0,
        ],
        alternator_online=True,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    status = EngineSensorStatus(
        rpm=healthy,
        volts=healthy,
        amps=healthy,
        oil_pressure=healthy,
        oil_temperature=healthy,
        fuel_pressure=healthy,
        fuel_flow=healthy,
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

    result = analyzer.analyze(
        engine,
        sensor_status=status,
    )

    assert result.severity == "CRITICAL"
    assert result.hottest_cylinder == 3
    assert result.hottest_cht_f == 460.0