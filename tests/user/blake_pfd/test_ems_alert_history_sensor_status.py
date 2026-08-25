from __future__ import annotations

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.ems_alert_history import EmsAlertHistory
from pyefis.user.blake_pfd.engine_data import EngineData


def test_invalid_hot_cht_does_not_enter_alert_history(tmp_path) -> None:
    history = EmsAlertHistory()

    history.log_dir = tmp_path
    history.log_path = tmp_path / "ems_alert_history.csv"

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
        alternator_online=True,
        ignition_a=True,
        ignition_b=True,
        fuel_remaining_gal=20.0,
        endurance_hr=3.0,
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

    history.update(
        engine,
        sensor_status=status,
    )

    assert "HIGH CHT" not in history.active_alerts
    assert "CHT" not in history.active_alerts
    assert len(history.alerts) == 0