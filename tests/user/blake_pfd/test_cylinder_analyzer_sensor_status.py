from __future__ import annotations

from pyefis.user.blake_pfd.core.cylinder_analyzer import (
    CylinderAnalyzer,
)
from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_invalid_cht_probe_does_not_create_false_imbalance() -> None:
    analyzer = CylinderAnalyzer()

    engine = EngineData(
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

    assert result.imbalance_detected is False
    assert result.hottest_cht_f == 355.0
    assert result.hottest_cylinder == 2