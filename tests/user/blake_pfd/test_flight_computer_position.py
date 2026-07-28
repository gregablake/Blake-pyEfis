from types import SimpleNamespace

from pyefis.user.blake_pfd.flight_computer import (
    FlightComputer,
    safe_latitude,
    safe_longitude,
)


def test_safe_position_helpers() -> None:
    assert safe_latitude(39.36) == 39.36
    assert safe_longitude(-84.52) == -84.52

    assert safe_latitude(91.0) is None
    assert safe_longitude(-181.0) is None

    assert safe_latitude(None) is None
    assert safe_longitude("bad") is None


def test_flight_computer_preserves_gps_position() -> None:
    computer = FlightComputer()

    raw = SimpleNamespace(
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

    result = computer.update(raw)

    assert result.position_valid is True
    assert result.latitude_deg == 39.3638
    assert result.longitude_deg == -84.5220


def test_zero_zero_position_is_invalid() -> None:
    computer = FlightComputer()

    raw = SimpleNamespace(
        differential_pressure_pa=0.0,
        static_pressure_pa=101325.0,
        outside_air_temp_c=15.0,
        heading_deg=0.0,
        gps_track_deg=0.0,
        gps_ground_speed_kt=0.0,
        gps_lat_deg=0.0,
        gps_lon_deg=0.0,
        yaw_rate_deg_s=0.0,
        accel_y_g=0.0,
        accel_z_g=1.0,
        desired_track_deg=0.0,
    )

    result = computer.update(raw)

    assert result.position_valid is False
    assert result.distance_to_waypoint_nm == 0.0