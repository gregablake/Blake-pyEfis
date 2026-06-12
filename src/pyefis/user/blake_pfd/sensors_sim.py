from __future__ import annotations

from dataclasses import dataclass
from math import sin
from time import monotonic

from pyefis.user.blake_pfd.config_loader import load_config


@dataclass
class RawSensorData:
    differential_pressure_pa: float = 250.0
    static_pressure_pa: float = 101325.0
    outside_air_temp_c: float = 15.0

    heading_deg: float = 90.0
    gps_track_deg: float = 90.0
    gps_ground_speed_kt: float = 95.0

    yaw_rate_deg_s: float = 0.0
    accel_y_g: float = 0.0
    accel_z_g: float = 1.0

    waypoint_bearing_deg: float = 90.0
    desired_track_deg: float = 90.0
    cdi_deflection_nm: float = 0.0
    vdi_deflection_deg: float = 0.0

    gps_lat_deg: float = 39.1031
    gps_lon_deg: float = -84.5120


class SimulatedSensorSource:
    def __init__(self) -> None:
        self.start_time_s = monotonic()
        self.config = load_config()

    def read(self) -> RawSensorData:
        elapsed_s = monotonic() - self.start_time_s

        indicated_airspeed_kt = 95.0 + (sin(elapsed_s * 0.35) * 5.0)
        altitude_ft = 1200.0 + (sin(elapsed_s * 0.18) * 80.0)
        heading_deg = 90.0 + (sin(elapsed_s * 0.12) * 8.0)
        gps_track_deg = heading_deg
        gps_ground_speed_kt = indicated_airspeed_kt + 3.0
        yaw_rate_deg_s = sin(elapsed_s * 0.4) * 0.6

        gps_lat_deg = 39.1031
        gps_lon_deg = -84.5120

        profile = self.config.simulation.profile

        if profile == "climb":
            altitude_ft += elapsed_s * 8.0

        elif profile == "descent":
            altitude_ft -= elapsed_s * 6.0

        elif profile == "left_turn":
            heading_deg -= elapsed_s * 3.0
            gps_track_deg = heading_deg
            yaw_rate_deg_s = -3.0

        elif profile == "right_turn":
            heading_deg += elapsed_s * 3.0
            gps_track_deg = heading_deg
            yaw_rate_deg_s = 3.0

        elif profile == "approach":
            altitude_ft = max(700.0, 3500.0 - elapsed_s * 12.0)
            indicated_airspeed_kt = 85.0
            gps_ground_speed_kt = 82.0

        static_pressure_pa = altitude_to_pressure_pa(altitude_ft)
        differential_pressure_pa = ias_to_differential_pressure_pa(indicated_airspeed_kt)

        return RawSensorData(
            differential_pressure_pa=differential_pressure_pa,
            static_pressure_pa=static_pressure_pa,
            outside_air_temp_c=15.0,
            heading_deg=heading_deg % 360.0,
            gps_track_deg=gps_track_deg % 360.0,
            gps_ground_speed_kt=gps_ground_speed_kt,
            yaw_rate_deg_s=yaw_rate_deg_s,
            accel_y_g=0.05 if abs(yaw_rate_deg_s) > 1.0 else 0.0,
            accel_z_g=1.0,
            waypoint_bearing_deg=90.0,
            desired_track_deg=90.0,
            cdi_deflection_nm=sin(elapsed_s * 0.15) * 0.4,
            vdi_deflection_deg=sin(elapsed_s * 0.10) * 0.4,
            gps_lat_deg=gps_lat_deg,
            gps_lon_deg=gps_lon_deg,
        )


def altitude_to_pressure_pa(altitude_ft: float) -> float:
    return 101325.0 * (1.0 - altitude_ft / 145366.45) ** (1.0 / 0.190284)


def ias_to_differential_pressure_pa(ias_kt: float) -> float:
    knots_per_mps = 1.943844
    air_density_sea_level = 1.225

    airspeed_mps = ias_kt / knots_per_mps
    return 0.5 * air_density_sea_level * airspeed_mps ** 2