from __future__ import annotations

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.core.engine_trend_manager import (
    EngineTrendManager,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_invalid_hot_cht_is_not_added_to_trend_history() -> None:
    manager = EngineTrendManager()

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
    )

    result = manager.update(
        EngineData(
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
        ),
        sensor_status=status,
    )

    assert result.current_cht == 355.0
    assert result.predicted_cht == 355.0
    assert result.warning == ""