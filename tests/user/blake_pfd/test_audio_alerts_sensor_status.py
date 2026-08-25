from __future__ import annotations

from pyefis.user.blake_pfd.audio_alerts import (
    AudioAlertManager,
)
from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_invalid_hot_cht_does_not_trigger_audio_alert() -> None:
    manager = AudioAlertManager(
        enabled=True,
        buzzer_enabled=False,
        repeat_interval_s=10.0,
    )

    played: list[str] = []

    manager.play_alert = played.append

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

    manager.update(
        engine,
        sensor_status=status,
    )

    assert played == []
    assert manager.last_alert_text is None
    
def test_reset_clears_previous_audio_alert_state() -> None:
    manager = AudioAlertManager(
        enabled=True,
        buzzer_enabled=False,
        repeat_interval_s=10.0,
    )

    manager.last_alert_text = "HIGH CHT"
    manager.last_alert_time_s = 123.0

    manager.reset()

    assert manager.last_alert_text is None
    assert manager.last_alert_time_s == 0.0