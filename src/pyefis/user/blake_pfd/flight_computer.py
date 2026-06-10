from __future__ import annotations
from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin, sqrt
from time import monotonic

from pyefis.user.blake_pfd.airdata_calculations import (
    indicated_airspeed_from_dp,
    pressure_altitude,
)
from pyefis.user.blake_pfd.config_loader import get_cdi_full_scale_nm, load_config
from pyefis.user.blake_pfd.database_importer import AviationDatabase
from pyefis.user.blake_pfd.nav_math import NavPoint, calculate_nav_solution
from pyefis.user.blake_pfd.performance_calculations import (
    wind_from_heading_track,
)
from pyefis.user.blake_pfd.route_manager import RouteManager

KNOTS_PER_MPS = 1.943844
PA_STANDARD_SEA_LEVEL = 101325.0


@dataclass
class FlightData:
    ias_kt: float = 0.0
    tas_kt: float = 0.0

    pressure_alt_ft: float = 0.0
    density_alt_ft: float = 0.0
    vsi_fpm: float = 0.0

    heading_deg: float = 0.0
    track_deg: float = 0.0
    ground_speed_kt: float = 0.0

    wind_speed_kt: float = 0.0
    wind_direction_deg: float = 0.0

    turn_rate_deg_sec: float = 0.0
    slip_skid: float = 0.0

    bearing_deg: float = 0.0
    desired_track_deg: float = 0.0
    cdi: float = 0.0
    vdi: float = 0.0
    distance_to_waypoint_nm: float = 0.0
    course_error_deg: float = 0.0

class FlightComputer:
    def __init__(self) -> None:
        self.last_alt_ft: float | None = None
        self.last_time_s: float | None = None
        self.vsi_fpm: float = 0.0
        self.config = load_config()
        self.database = AviationDatabase()
        self.database.load_all()
        self.route_manager = RouteManager()
        
    def update(self, raw) -> FlightData:
        flight = FlightData()

        flight.ias_kt = indicated_airspeed_from_dp(raw.differential_pressure_pa)
        flight.pressure_alt_ft = pressure_altitude(raw.static_pressure_pa)
        flight.vsi_fpm = self.calculate_vsi(flight.pressure_alt_ft)

        flight.tas_kt = estimate_true_airspeed_kt(
            flight.ias_kt,
            flight.pressure_alt_ft,
            raw.outside_air_temp_c,
        )

        flight.density_alt_ft = estimate_density_altitude_ft(
            flight.pressure_alt_ft,
            raw.outside_air_temp_c,
        )

        flight.heading_deg = normalize_degrees(raw.heading_deg)
        flight.track_deg = normalize_degrees(raw.gps_track_deg)
        flight.ground_speed_kt = raw.gps_ground_speed_kt

        flight.wind_speed_kt, flight.wind_direction_deg = wind_from_heading_track(
            tas_kt=flight.tas_kt,
            heading_deg=flight.heading_deg,
            ground_speed_kt=flight.ground_speed_kt,
            track_deg=flight.track_deg,
        )
        flight.turn_rate_deg_sec = raw.yaw_rate_deg_s
        flight.slip_skid = calculate_slip_skid(raw.accel_y_g, raw.accel_z_g)

        airport = self.database.get_airport(self.config.navigation.selected_waypoint_id)

        if airport is not None:
            waypoint = NavPoint(
                ident=airport.ident,
                name=airport.name,
                lat_deg=airport.lat_deg,
                lon_deg=airport.lon_deg,
                elevation_ft=airport.elevation_ft,
            )
        else:
            waypoint = NavPoint(
                ident=self.config.navigation.selected_waypoint_id,
                name=self.config.navigation.selected_waypoint_name,
                lat_deg=self.config.navigation.selected_waypoint_lat,
                lon_deg=self.config.navigation.selected_waypoint_lon,
                elevation_ft=0.0,
            )

        active_leg = self.route_manager.get_active_leg()
        desired_track = raw.desired_track_deg or flight.track_deg

        if active_leg is not None:
            desired_track = active_leg.desired_track_deg

        nav = calculate_nav_solution(
            aircraft_lat_deg=getattr(raw, "gps_lat_deg", 39.10),
            aircraft_lon_deg=getattr(raw, "gps_lon_deg", -84.50),
            aircraft_alt_ft=flight.pressure_alt_ft,
            waypoint=waypoint,
            desired_track_deg=desired_track,
            cdi_full_scale_nm=get_cdi_full_scale_nm(self.config),
        )
            
        

        flight.bearing_deg = nav.bearing_to_wp_deg
        flight.desired_track_deg = nav.desired_track_deg
        flight.distance_to_waypoint_nm = nav.distance_to_wp_nm
        if self.config.route.auto_sequence:
            self.route_manager.maybe_advance_leg(
                distance_to_waypoint_nm=nav.distance_to_wp_nm,
                sequence_distance_nm=self.config.route.sequence_distance_nm,
    )
        flight.course_error_deg = nav.course_error_deg
        flight.cdi = nav.cdi_deflection_nm
        flight.vdi = nav.vdi_deflection_deg

        return flight
    
    def calculate_vsi(self, current_alt_ft: float) -> float:
        now_s = monotonic()

        if self.last_alt_ft is None or self.last_time_s is None:
            self.last_alt_ft = current_alt_ft
            self.last_time_s = now_s
            return 0.0

        dt_s = now_s - self.last_time_s

        if dt_s <= 0.05:
            return self.vsi_fpm

        raw_vsi = ((current_alt_ft - self.last_alt_ft) / dt_s) * 60.0

        alpha = 0.15
        self.vsi_fpm = (alpha * raw_vsi) + ((1.0 - alpha) * self.vsi_fpm)

        self.last_alt_ft = current_alt_ft
        self.last_time_s = now_s

        return self.vsi_fpm


def differential_pressure_to_ias_kt(dp_pa: float) -> float:
    dp_pa = max(dp_pa, 0.0)
    air_density_sea_level = 1.225
    airspeed_mps = sqrt((2.0 * dp_pa) / air_density_sea_level)
    return airspeed_mps * KNOTS_PER_MPS


def pressure_to_altitude_ft(static_pressure_pa: float) -> float:
    pressure = max(static_pressure_pa, 1.0)
    return 145366.45 * (1.0 - (pressure / PA_STANDARD_SEA_LEVEL) ** 0.190284)


def estimate_true_airspeed_kt(
    ias_kt: float,
    pressure_alt_ft: float,
    oat_c: float,
) -> float:
    altitude_correction = 1.0 + (0.02 * (pressure_alt_ft / 1000.0))
    temp_correction = 1.0 + ((oat_c - 15.0) * 0.001)
    return ias_kt * altitude_correction * temp_correction


def estimate_density_altitude_ft(
    pressure_alt_ft: float,
    oat_c: float,
) -> float:
    isa_temp_c = 15.0 - (1.98 * (pressure_alt_ft / 1000.0))
    return pressure_alt_ft + (120.0 * (oat_c - isa_temp_c))


def estimate_wind(
    true_airspeed_kt: float,
    heading_deg: float,
    ground_speed_kt: float,
    track_deg: float,
) -> tuple[float, float]:
    heading_rad = radians(heading_deg)
    track_rad = radians(track_deg)

    air_north = true_airspeed_kt * cos(heading_rad)
    air_east = true_airspeed_kt * sin(heading_rad)

    ground_north = ground_speed_kt * cos(track_rad)
    ground_east = ground_speed_kt * sin(track_rad)

    wind_north = ground_north - air_north
    wind_east = ground_east - air_east

    wind_speed = sqrt((wind_north ** 2) + (wind_east ** 2))

    wind_to_deg = degrees(atan2(wind_east, wind_north))
    wind_from_deg = normalize_degrees(wind_to_deg + 180.0)

    return wind_speed, wind_from_deg


def calculate_slip_skid(accel_y_g: float, accel_z_g: float) -> float:
    if abs(accel_z_g) < 0.05:
        return 0.0

    slip = accel_y_g / abs(accel_z_g)
    return max(-1.0, min(1.0, slip))


def normalize_degrees(value: float) -> float:
    return value % 360.0