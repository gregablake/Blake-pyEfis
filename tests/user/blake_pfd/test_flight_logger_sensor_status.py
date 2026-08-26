from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.flight_logger import FlightLogger


class RecordingFlightLogger(FlightLogger):
    def __init__(self) -> None:
        super().__init__(log_interval_s=0.0)
        self.rows: list[dict] = []

    def write_row(self, row: dict) -> None:
        self.rows.append(row)


def make_pfd():
    return SimpleNamespace(
        __dict__={}
    )


def test_logger_preserves_raw_value_and_records_invalid_status() -> None:
    logger = RecordingFlightLogger()

    engine = EngineData(
        rpm=9000.0,
        volts=14.2,
        amps=5.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[350.0] * 6,
        egt_f=[1350.0, 1360.0],
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
        rpm=invalid,
        volts=healthy,
        amps=healthy,
        oil_pressure=healthy,
        oil_temperature=healthy,
        fuel_pressure=healthy,
        fuel_flow=healthy,
        cht=(healthy,) * 6,
        egt=(healthy,) * 2,
    )

    # asdict() requires a dataclass-like PFD object.
    from pyefis.user.blake_pfd.flight_computer import FlightData

    pfd = FlightData()

    logger.maybe_log(
        pfd,
        waypoint_id="TEST",
        engine=engine,
        sensor_status=status,
    )

    row = logger.rows[0]

    assert row["engine_rpm"] == 9000.0
    assert row["engine_rpm_valid"] is False
    assert row["engine_rpm_fresh"] is False

    assert row["engine_volts"] == 14.2
    assert row["engine_volts_valid"] is True
    assert row["engine_volts_fresh"] is True


def test_logger_records_per_probe_cht_and_egt_status() -> None:
    logger = RecordingFlightLogger()

    from pyefis.user.blake_pfd.flight_computer import FlightData

    pfd = FlightData()

    engine = EngineData(
        cht_f=[
            350.0,
            351.0,
            700.0,
            353.0,
            354.0,
            355.0,
        ],
        egt_f=[
            1350.0,
            2500.0,
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
            invalid,
        ),
    )

    logger.maybe_log(
        pfd,
        waypoint_id="TEST",
        engine=engine,
        sensor_status=status,
    )

    row = logger.rows[0]

    assert row["engine_cht_3"] == 700.0
    assert row["engine_cht_3_valid"] is False
    assert row["engine_cht_3_fresh"] is False

    assert row["engine_cht_2_valid"] is True
    assert row["engine_cht_2_fresh"] is True

    assert row["engine_egt_2"] == 2500.0
    assert row["engine_egt_2_valid"] is False
    assert row["engine_egt_2_fresh"] is False


def test_logger_marks_status_unknown_when_status_not_supplied() -> None:
    logger = RecordingFlightLogger()

    from pyefis.user.blake_pfd.flight_computer import FlightData

    logger.maybe_log(
        FlightData(),
        waypoint_id="TEST",
        engine=EngineData(),
        sensor_status=None,
    )

    row = logger.rows[0]

    assert row["engine_rpm_valid"] == ""
    assert row["engine_rpm_fresh"] == ""
    assert row["engine_cht_1_valid"] == ""
    assert row["engine_egt_1_fresh"] == ""
