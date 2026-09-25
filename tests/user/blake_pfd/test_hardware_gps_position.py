from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.hardware_readers import (
    BlakeHardwareSensorSource,
    GpsReader,
    HardwareStatus,
)


class FakeGpsReport:
    track = 123.0
    speed = 25.0
    lat = 39.3638
    lon = -84.5220

    def get(self, key, default=None):
        if key == "class":
            return "TPV"
        return default


class FakeGpsSession:
    def next(self):
        return FakeGpsReport()


def test_gps_reader_preserves_latitude_and_longitude() -> None:
    reader = GpsReader.__new__(GpsReader)

    reader.ok = True
    reader.gps_session = FakeGpsSession()
    reader.last_success_s = None
    reader.last_track_deg = 0.0
    reader.last_ground_speed_kt = 0.0

    reader.selected_waypoint_lat = 39.1031
    reader.selected_waypoint_lon = -84.5120
    reader.desired_track_deg = 0.0

    result = reader.read()

    assert result["gps_lat_deg"] == 39.3638
    assert result["gps_lon_deg"] == -84.5220


class StubReader:
    def __init__(self, result):
        self.result = result
        self.ok = True
        self.last_success_s = 10.0

    def read(self):
        return self.result


def test_hardware_source_forwards_gps_position() -> None:
    source = BlakeHardwareSensorSource.__new__(
        BlakeHardwareSensorSource
    )

    source.bno085 = StubReader(
        {
            "pitch_deg": 1.0,
            "roll_deg": 2.0,
            "heading_deg": 3.0,
            "yaw_rate_deg_s": 0.0,
            "accel_x_g": 0.0,
            "accel_y_g": 0.0,
            "accel_z_g": 1.0,
        }
    )

    source.baro = StubReader(
        {
            "static_pressure_pa": 101325.0,
            "outside_air_temp_c": 15.0,
        }
    )

    source.airspeed = StubReader(
        {
            "differential_pressure_pa": 100.0,
        }
    )

    source.gps = StubReader(
        {
            "gps_track_deg": 123.0,
            "gps_ground_speed_kt": 48.6,
            "gps_lat_deg": 39.3638,
            "gps_lon_deg": -84.5220,
            "waypoint_bearing_deg": 180.0,
            "desired_track_deg": 170.0,
            "cdi_deflection_nm": 0.0,
            "vdi_deflection_deg": 0.0,
        }
    )

    source.status = HardwareStatus()

    raw = source.read()

    assert raw.gps_lat_deg == 39.3638
    assert raw.gps_lon_deg == -84.5220


def test_invalid_gps_fix_keeps_last_position_without_refreshing() -> None:
    from unittest.mock import patch

    class InvalidGpsReport:
        track = 124.0
        speed = 20.0
        lat = 0.0
        lon = 0.0

        def get(self, key, default=None):
            if key == "class":
                return "TPV"
            return default

    class InvalidGpsSession:
        def next(self):
            return InvalidGpsReport()

    reader = GpsReader.__new__(GpsReader)

    reader.ok = True
    reader.gps_session = InvalidGpsSession()
    reader.last_success_s = 25.0
    reader.last_track_deg = 123.0
    reader.last_ground_speed_kt = 40.0
    reader.last_lat_deg = 39.3638
    reader.last_lon_deg = -84.5220

    reader.selected_waypoint_lat = 39.1031
    reader.selected_waypoint_lon = -84.5120
    reader.desired_track_deg = 0.0

    with patch(
        "pyefis.user.blake_pfd.hardware_readers.monotonic"
    ) as monotonic_mock:
        result = reader.read()

    assert result["gps_lat_deg"] == 39.3638
    assert result["gps_lon_deg"] == -84.5220

    # An invalid position must not masquerade as a fresh GPS fix.
    assert reader.last_success_s == 25.0
    monotonic_mock.assert_not_called()


def test_valid_gps_fix_recovers_and_refreshes_timestamp() -> None:
    from unittest.mock import patch

    class RecoveryGpsReport:
        track = 140.0
        speed = 30.0
        lat = 39.4000
        lon = -84.6000

        def get(self, key, default=None):
            if key == "class":
                return "TPV"
            return default

    class RecoveryGpsSession:
        def next(self):
            return RecoveryGpsReport()

    reader = GpsReader.__new__(GpsReader)

    reader.ok = True
    reader.gps_session = RecoveryGpsSession()
    reader.last_success_s = 25.0
    reader.last_track_deg = 123.0
    reader.last_ground_speed_kt = 40.0
    reader.last_lat_deg = 39.3638
    reader.last_lon_deg = -84.5220

    reader.selected_waypoint_lat = 39.1031
    reader.selected_waypoint_lon = -84.5120
    reader.desired_track_deg = 0.0

    with patch(
        "pyefis.user.blake_pfd.hardware_readers.monotonic",
        return_value=50.0,
    ):
        result = reader.read()

    assert result["gps_lat_deg"] == 39.4000
    assert result["gps_lon_deg"] == -84.6000

    assert reader.last_lat_deg == 39.4000
    assert reader.last_lon_deg == -84.6000
    assert reader.last_success_s == 50.0


def test_gps_recovers_after_transient_read_exception() -> None:
    class TransientGpsSession:
        def __init__(self) -> None:
            self.calls = 0

        def next(self):
            self.calls += 1

            if self.calls == 1:
                raise OSError("temporary gpsd read failure")

            return FakeGpsReport()

    session = TransientGpsSession()

    reader = GpsReader.__new__(GpsReader)

    reader.ok = True
    reader.gps_session = session
    reader.last_success_s = None
    reader.last_track_deg = 0.0
    reader.last_ground_speed_kt = 0.0
    reader.last_lat_deg = 0.0
    reader.last_lon_deg = 0.0

    reader.selected_waypoint_lat = 39.1031
    reader.selected_waypoint_lon = -84.5120
    reader.desired_track_deg = 0.0

    first = reader.read()

    assert first["gps_lat_deg"] == 0.0
    assert first["gps_lon_deg"] == 0.0

    # A transient read error must not permanently disable an
    # otherwise-live gpsd session.
    second = reader.read()

    assert session.calls == 2
    assert second["gps_lat_deg"] == 39.3638
    assert second["gps_lon_deg"] == -84.5220
    assert reader.ok is True
