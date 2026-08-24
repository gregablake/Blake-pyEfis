from __future__ import annotations

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)


def test_engine_sensor_status_defaults_fail_closed() -> None:
    status = EngineSensorStatus()

    assert status.rpm.valid is False
    assert status.rpm.fresh is False

    assert status.oil_pressure.valid is False
    assert status.oil_pressure.fresh is False

    assert len(status.cht) == 6
    assert len(status.egt) == 2

    assert all(
        channel.valid is False
        for channel in status.cht
    )
    assert all(
        channel.fresh is False
        for channel in status.cht
    )


def test_engine_channel_status_can_be_marked_healthy() -> None:
    status = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    assert status.valid is True
    assert status.fresh is True
    assert status.message == "DATA VALID"