from __future__ import annotations

import csv
from types import SimpleNamespace

import pytest

from pyefis.user.blake_pfd.core.sensor_manager import (
    SensorManager,
)
from pyefis.user.blake_pfd.engine_data import (
    EngineData,
)
from pyefis.user.blake_pfd.flight_computer import (
    FlightComputer,
    FlightData,
)
from pyefis.user.blake_pfd.flight_logger import (
    FlightLogger,
)
from pyefis.user.blake_pfd.log_replay import (
    LogReplaySource,
)


class RecordingFlightLogger(FlightLogger):
    def __init__(self) -> None:
        super().__init__(
            log_interval_s=0.0,
        )
        self.rows: list[dict] = []

    def write_row(
        self,
        row: dict,
    ) -> None:
        self.rows.append(row)


def make_raw() -> SimpleNamespace:
    return SimpleNamespace(
        differential_pressure_pa=0.0,
        static_pressure_pa=101325.0,
        outside_air_temp_c=15.0,
        heading_deg=0.0,
        gps_track_deg=0.0,
        gps_ground_speed_kt=0.0,
        gps_lat_deg=39.3638,
        gps_lon_deg=-84.5220,
        yaw_rate_deg_s=0.0,
        accel_y_g=0.0,
        accel_z_g=1.0,
        desired_track_deg=0.0,
    )


def write_log(
    path,
    row: dict,
) -> None:
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file_handle:
        writer = csv.DictWriter(
            file_handle,
            fieldnames=list(
                row.keys()
            ),
        )
        writer.writeheader()
        writer.writerow(row)


def test_live_flight_frame_records_selected_baro():
    computer = FlightComputer()

    assert (
        computer.baro_setting_controller
        .set_setting(30.12)
        is True
    )

    result = computer.update(
        make_raw()
    )

    assert (
        result.baro_setting_inhg
        == pytest.approx(30.12)
    )


def test_logger_records_indicated_altitude_and_baro():
    logger = RecordingFlightLogger()

    pfd = FlightData(
        pressure_alt_ft=1500.0,
        indicated_alt_ft=1675.0,
        baro_setting_inhg=30.12,
    )

    logger.maybe_log(
        pfd,
        waypoint_id="TEST",
        engine=EngineData(),
    )

    row = logger.rows[0]

    assert (
        row["pressure_alt_ft"]
        == 1500.0
    )

    assert (
        row["indicated_alt_ft"]
        == 1675.0
    )

    assert (
        row["baro_setting_inhg"]
        == 30.12
    )


def test_replay_restores_indicated_altitude_and_baro(
    tmp_path,
):
    path = (
        tmp_path
        / "baro_replay.csv"
    )

    write_log(
        path,
        {
            "pressure_alt_ft": "1500.0",
            "indicated_alt_ft": "1675.0",
            "baro_setting_inhg": "30.12",
        },
    )

    result = LogReplaySource(
        path,
    ).read()

    assert (
        result.pressure_alt_ft
        == pytest.approx(1500.0)
    )

    assert (
        result.indicated_alt_ft
        == pytest.approx(1675.0)
    )

    assert (
        result.baro_setting_inhg
        == pytest.approx(30.12)
    )


def test_legacy_replay_uses_safe_altitude_and_baro_fallbacks(
    tmp_path,
):
    path = (
        tmp_path
        / "legacy_replay.csv"
    )

    write_log(
        path,
        {
            "pressure_alt_ft": "2500.0",
        },
    )

    result = LogReplaySource(
        path,
    ).read()

    # Old logs did not contain indicated altitude.
    # Preserve useful altitude instead of replaying 0 ft.
    assert (
        result.indicated_alt_ft
        == pytest.approx(2500.0)
    )

    # Old logs did not contain pilot BARO selection.
    # Use standard pressure as the explicit fallback.
    assert (
        result.baro_setting_inhg
        == pytest.approx(29.92)
    )


@pytest.mark.parametrize(
    "bad_baro",
    [
        "",
        "nan",
        "inf",
        "-inf",
        "27.49",
        "31.51",
        "not-a-number",
    ],
)
def test_invalid_replay_baro_falls_back_to_standard(
    tmp_path,
    bad_baro,
):
    path = (
        tmp_path
        / "invalid_baro.csv"
    )

    write_log(
        path,
        {
            "pressure_alt_ft": "1500.0",
            "indicated_alt_ft": "1500.0",
            "baro_setting_inhg": bad_baro,
        },
    )

    result = LogReplaySource(
        path,
    ).read()

    assert (
        result.baro_setting_inhg
        == pytest.approx(29.92)
    )


def test_sensor_manager_syncs_runtime_baro_from_replay(
    tmp_path,
):
    path = (
        tmp_path
        / "sensor_manager_replay.csv"
    )

    write_log(
        path,
        {
            "pressure_alt_ft": "1500.0",
            "indicated_alt_ft": "1675.0",
            "baro_setting_inhg": "30.12",
        },
    )

    computer = FlightComputer()

    assert (
        computer.baro_setting_controller
        .setting_inhg
        == pytest.approx(29.92)
    )

    manager = SensorManager(
        flight_computer=computer,
        replay_log=str(path),
    )

    result = manager.read_flight()

    assert (
        result.baro_setting_inhg
        == pytest.approx(30.12)
    )

    assert (
        computer.baro_setting_controller
        .setting_inhg
        == pytest.approx(30.12)
    )
