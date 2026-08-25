from __future__ import annotations

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.ems_trend_page import EmsTrendPage
from pyefis.user.blake_pfd.engine_data import EngineData


def test_trend_page_retains_sensor_status_with_sample() -> None:
    page = EmsTrendPage()

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

    engine = EngineData(
        rpm=2450.0,
        volts=14.2,
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
    )

    status = EngineSensorStatus(
        rpm=healthy,
        volts=healthy,
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

    page.add_sample(
        engine,
        sensor_status=status,
    )

    assert len(page.samples) == 1
    assert len(page.sensor_statuses) == 1
    assert page.sensor_statuses[0] is status