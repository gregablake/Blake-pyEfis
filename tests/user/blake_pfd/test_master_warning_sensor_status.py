from __future__ import annotations

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.master_warning import (
    get_engine_warnings,
)


def test_invalid_hot_cht_does_not_create_master_warning() -> None:
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

    warnings = get_engine_warnings(
        engine,
        sensor_status=status,
    )

    warning_texts = [
        warning.text
        for warning in warnings
    ]

    assert "HIGH CHT" not in warning_texts
    assert "CHT" not in warning_texts
def test_invalid_electrical_status_does_not_create_alt_fail_warning() -> None:
    engine = EngineData(
        rpm=2450.0,
        volts=0.0,
        amps=0.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[350.0] * 6,
        egt_f=[1350.0, 1360.0],
        ignition_a=True,
        ignition_b=True,
        alternator_online=False,
        fuel_remaining_gal=20.0,
        endurance_hr=3.0,
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
        volts=invalid,
        amps=invalid,
        oil_pressure=healthy,
        oil_temperature=healthy,
        fuel_pressure=healthy,
        fuel_flow=healthy,
        cht=(healthy,) * 6,
        egt=(healthy,) * 2,
    )

    warnings = get_engine_warnings(
        engine,
        sensor_status=status,
    )

    texts = [warning.text for warning in warnings]

    assert "ALT FAIL" not in texts


def test_valid_electrical_status_still_creates_alt_fail_warning() -> None:
    engine = EngineData(
        rpm=2450.0,
        volts=14.2,
        amps=5.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[350.0] * 6,
        egt_f=[1350.0, 1360.0],
        ignition_a=True,
        ignition_b=True,
        alternator_online=False,
        fuel_remaining_gal=20.0,
        endurance_hr=3.0,
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
        cht=(healthy,) * 6,
        egt=(healthy,) * 2,
    )

    warnings = get_engine_warnings(
        engine,
        sensor_status=status,
    )

    texts = [warning.text for warning in warnings]

    assert "ALT FAIL" in texts
