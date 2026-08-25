from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_advisor import (
    EngineAdvisor,
)
from pyefis.user.blake_pfd.core.engine_manager import (
    EngineHealth,
)
from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_invalid_low_oil_pressure_does_not_mislabel_other_critical_condition() -> None:
    advisor = EngineAdvisor()

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
        oil_pressure=invalid,
        oil_temperature=healthy,
        cht=(
            healthy,
            healthy,
            healthy,
            healthy,
            healthy,
            healthy,
        ),
    )

    engine_state = SimpleNamespace(
        data=EngineData(
            oil_pressure_psi=0.0,
            oil_temp_f=190.0,
            cht_f=[
                460.0,
                350.0,
                350.0,
                350.0,
                350.0,
                350.0,
            ],
        ),
        health=EngineHealth(
            health_score=65,
            cht_max_f=460.0,
            status="CRITICAL",
        ),
        prediction=None,
        cylinders=None,
    )

    result = advisor.advise(
        engine_state,
        sensor_status=status,
    )

    assert result.severity == "CRITICAL"
    assert result.title == "Engine Health Advisor"