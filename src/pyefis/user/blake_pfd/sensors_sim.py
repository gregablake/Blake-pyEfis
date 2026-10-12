from __future__ import annotations

import os

from dataclasses import dataclass
from math import asin, atan2, cos, degrees, hypot, radians, sin, sqrt
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
        self.last_reset_counter = self.config.simulation.reset_counter
        # Route distance is integrated from reported GS in demo mode only.
        self._scenic_progress_nm = 0.0
        self._scenic_last_sample_s = self.start_time_s

    def read(self) -> RawSensorData:
        self.config = load_config()
        now_s = monotonic()
        if self.last_reset_counter != self.config.simulation.reset_counter:
            self.start_time_s = now_s
            self.last_reset_counter = self.config.simulation.reset_counter
            self._scenic_progress_nm = 0.0
            self._scenic_last_sample_s = now_s
        if self.config.simulation.paused:
            elapsed_s = 0.0
        else:
            elapsed_s = now_s - self.start_time_s

        indicated_airspeed_kt = 95.0 + (sin(elapsed_s * 0.35) * 5.0)
        altitude_ft = 1200.0 + (sin(elapsed_s * 0.18) * 80.0)
        heading_deg = 90.0 + (sin(elapsed_s * 0.12) * 8.0)
        gps_track_deg = heading_deg
        gps_ground_speed_kt = indicated_airspeed_kt + 3.0
        yaw_rate_deg_s = sin(elapsed_s * 0.4) * 0.6

        gps_lat_deg = 39.1031
        gps_lon_deg = -84.5120

        # BLAKE_PFD_MOVING_ROUTE_DEMO_V3
        # Opt-in development scenario ONLY, never hardware-mode input.
        # Position advances at the reported groundspeed, stays frozen
        # while paused, and resets on simulation.reset_counter changes.
        # Route loops visibly at KCVG for repeat demonstrations (~12 min).
        # All SRTM, FAA, freshness gates, and alerts remain unchanged.
        if os.environ.get("BLAKE_PFD_SCENIC_DEMO") == "1":
            sample_interval_s = max(
                0.0, now_s - self._scenic_last_sample_s
            )
            self._scenic_last_sample_s = now_s
            if not self.config.simulation.paused:
                self._scenic_progress_nm += (
                    gps_ground_speed_kt * sample_interval_s / 3600.0
                )
            scenic_distance_nm = _scenic_route_distance_nm()
            if scenic_distance_nm > 0.0:
                # Explicit DEMO LOOP, not a continuous aircraft turn.
                self._scenic_progress_nm %= scenic_distance_nm
            gps_lat_deg, gps_lon_deg, scenic_bearing = (
                _scenic_route_position(self._scenic_progress_nm)
            )
            altitude_ft += 900.0  # 2100 +/- 80 ft MSL (level)
            heading_deg = scenic_bearing + 1.3 * sin(elapsed_s * 0.12)
            gps_track_deg = scenic_bearing

        # BLAKE_V5_REAL_MOUNTAIN_TEST: optional STATIONARY high-relief scene.
        # Requires real N40W106 SRTM data. No fabricated elevation values.
        # Normal and V3 Cincinnati modes are unchanged when opt-in is absent.
        if os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1":
            gps_lat_deg, gps_lon_deg = _MOUNTAIN_TEST_POSITION
            altitude_ft = _MOUNTAIN_TEST_ALTITUDE_FT + 60.0 * sin(elapsed_s * 0.07)
            heading_deg = _MOUNTAIN_TEST_HEADING_DEG
            gps_track_deg = heading_deg
            # BLAKE_V6_STATIC_GPS_SPEED: no motion in this camera scene.
            if os.environ.get("BLAKE_PFD_V6_VISUALS") == "1":
                gps_ground_speed_kt = 0.0

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

        # BLAKE_V7_TRUE_STATIC_MOUNTAIN: static camera has no simulated wind,
        # pitot airflow, or motion. Applies ONLY to opt-in V6+V7 test mode.
        # Cincinnati flight and normal simulation profiles remain untouched.
        if (
            os.environ.get("BLAKE_PFD_V7_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_V6_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
        ):
            altitude_ft = _MOUNTAIN_TEST_ALTITUDE_FT
            indicated_airspeed_kt = 0.0
            gps_ground_speed_kt = 0.0
            yaw_rate_deg_s = 0.0
            heading_deg = _MOUNTAIN_TEST_HEADING_DEG
            gps_track_deg = _MOUNTAIN_TEST_HEADING_DEG

        # BLAKE_V8_REAL_RIDGE_COMPARISON: lower stationary camera near Longs Peak.
        # Visual geometry comparison ONLY; no flight simulation or warning bypass.
        # Older V7 15,000-foot scene remains identical when this is disabled.
        if (
            os.environ.get("BLAKE_PFD_V8_RIDGE_DEMO") == "1"
            and os.environ.get("BLAKE_PFD_V7_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_V6_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
        ):
            altitude_ft = 12000.0
            heading_deg = 220.0  # Longs Peak, rather than the 240-degree baseline.
            gps_track_deg = 220.0  # Heading display only; GS remains zero.
            indicated_airspeed_kt = 0.0
            gps_ground_speed_kt = 0.0
            yaw_rate_deg_s = 0.0

        # V9 OPTIONAL HIGH RIDGE: exactly the same static GPS position and
        # 220-degree heading as the lower V8 ridge, but 15,000 ft MSL.
        # This is a comparison camera only; warning logic remains active.
        if (
            os.environ.get("BLAKE_PFD_V9_HIGH_RIDGE") == "1"
            and os.environ.get("BLAKE_PFD_V8_RIDGE_DEMO") == "1"
            and os.environ.get("BLAKE_PFD_V7_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_V6_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
        ):
            altitude_ft = 15000.0
            heading_deg = 220.0
            gps_track_deg = 220.0
            indicated_airspeed_kt = 0.0
            gps_ground_speed_kt = 0.0
            yaw_rate_deg_s = 0.0

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


# Rocky Mountain National Park / Longs Peak vicinity, real SRTM only.
# THIS IS A STATIC TEST SCENE, unrelated to the displayed flight plan.
_MOUNTAIN_TEST_POSITION = (40.3300, -105.5300)
_MOUNTAIN_TEST_ALTITUDE_FT = 15000.0
_MOUNTAIN_TEST_HEADING_DEG = 240.0


# An approximately 19 NM route starting just SW of KHAO toward KCVG.
# Great-circle interpolation is independent of the PFD's navigation state.
_SCENIC_START = (39.3450, -84.5320)
_SCENIC_END = (39.0488, -84.6678)
_EARTH_RADIUS_NM = 3440.065


def _scenic_route_distance_nm() -> float:
    lat1, lon1 = (radians(v) for v in _SCENIC_START)
    lat2, lon2 = (radians(v) for v in _SCENIC_END)
    a = (
        sin((lat2 - lat1) / 2.0) ** 2
        + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2.0) ** 2
    )
    return _EARTH_RADIUS_NM * 2.0 * asin(min(1.0, sqrt(a)))


def _scenic_route_position(distance_nm: float) -> tuple[float, float, float]:
    """Lat, lon, true bearing along the demo great-circle segment."""
    lat1, lon1 = (radians(v) for v in _SCENIC_START)
    lat2, lon2 = (radians(v) for v in _SCENIC_END)
    total_nm = _scenic_route_distance_nm()
    fraction = max(0.0, min(1.0, distance_nm / total_nm))
    angle = total_nm / _EARTH_RADIUS_NM
    if angle == 0.0:
        return (*_SCENIC_START, 200.0)
    weight1 = sin((1.0 - fraction) * angle) / sin(angle)
    weight2 = sin(fraction * angle) / sin(angle)
    x = weight1 * cos(lat1) * cos(lon1) + weight2 * cos(lat2) * cos(lon2)
    y = weight1 * cos(lat1) * sin(lon1) + weight2 * cos(lat2) * sin(lon2)
    z = weight1 * sin(lat1) + weight2 * sin(lat2)
    lat = atan2(z, hypot(x, y))
    lon = atan2(y, x)
    delta_lon = lon2 - lon
    bearing = degrees(atan2(
        sin(delta_lon) * cos(lat2),
        cos(lat) * sin(lat2) - sin(lat) * cos(lat2) * cos(delta_lon),
    )) % 360.0
    return degrees(lat), degrees(lon), bearing


def altitude_to_pressure_pa(altitude_ft: float) -> float:
    return 101325.0 * (1.0 - altitude_ft / 145366.45) ** (1.0 / 0.190284)


def ias_to_differential_pressure_pa(ias_kt: float) -> float:
    knots_per_mps = 1.943844
    air_density_sea_level = 1.225

    airspeed_mps = ias_kt / knots_per_mps
    return 0.5 * air_density_sea_level * airspeed_mps ** 2