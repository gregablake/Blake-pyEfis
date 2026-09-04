from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from pyefis.user.blake_pfd.airdata_calculations import (
    indicated_airspeed_from_dp,
    indicated_altitude,
    pressure_altitude,
)
from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.core.baro_setting_controller import (
    BaroSettingController,
)
from pyefis.user.blake_pfd.database_importer import AviationDatabase
from pyefis.user.blake_pfd.nav_math import NavPoint, calculate_nav_solution
from pyefis.user.blake_pfd.performance_calculations import (
    density_altitude_estimate,
    true_airspeed_estimate,
    wind_from_heading_track,
)
from pyefis.user.blake_pfd.route_manager import RouteManager


@dataclass
class FlightData:
    ias_kt: float = 0.0
    tas_kt: float = 0.0

    pressure_alt_ft: float = 0.0
    indicated_alt_ft: float = 0.0
    density_alt_ft: float = 0.0
    vsi_fpm: float = 0.0

    pitch_deg: float = 0.0
    roll_deg: float = 0.0

    heading_deg: float = 0.0
    track_deg: float = 0.0
    ground_speed_kt: float = 0.0
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    position_valid: bool = False

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
    
    glidepath_target_alt_ft: float = 0.0
    glidepath_alt_error_ft: float = 0.0


class FlightComputer:
    def __init__(self) -> None:
        self.last_alt_ft: float | None = None
        self.last_time_s: float | None = None
        self.vsi_fpm: float = 0.0

        self.config = load_config()

        self.baro_setting_controller = (
            BaroSettingController(
                initial_inhg=(
                    self.config.altitude
                    .baro_setting_inhg
                ),
            )
        )

        self.database = AviationDatabase()
        self.database.load_all()

        self.route_manager = RouteManager()

    def update(self, raw) -> FlightData:
        flight = FlightData()

        flight.ias_kt = indicated_airspeed_from_dp(
            raw.differential_pressure_pa
        )

        flight.pressure_alt_ft = pressure_altitude(
            raw.static_pressure_pa
        )

        flight.indicated_alt_ft = indicated_altitude(
            static_pa=raw.static_pressure_pa,
            baro_setting_inhg=(
                self.baro_setting_controller
                .setting_inhg
            ),
        )

        flight.vsi_fpm = self.calculate_vsi(
            flight.pressure_alt_ft
        )

        flight.tas_kt = true_airspeed_estimate(
            flight.ias_kt,
            flight.pressure_alt_ft,
            raw.outside_air_temp_c,
        )

        flight.density_alt_ft = density_altitude_estimate(
            flight.pressure_alt_ft,
            raw.outside_air_temp_c,
        )

        flight.pitch_deg = float(
            getattr(
                raw,
                "pitch_deg",
                0.0,
            )
        )

        flight.roll_deg = float(
            getattr(
                raw,
                "roll_deg",
                0.0,
            )
        )

        flight.heading_deg = normalize_degrees(
            raw.heading_deg
        )
        flight.track_deg = normalize_degrees(
            raw.gps_track_deg
        )
        flight.ground_speed_kt = (
            raw.gps_ground_speed_kt
        )
        
        latitude = safe_latitude(
            getattr(
                raw,
                "gps_lat_deg",
                None,
            )
        )

        longitude = safe_longitude(
            getattr(
                raw,
                "gps_lon_deg",
                None,
            )
        )

        flight.position_valid = (
            latitude is not None
            and longitude is not None
            and not (
                latitude == 0.0
                and longitude == 0.0
            )
        )

        flight.latitude_deg = (
            latitude
            if latitude is not None
            else 0.0
        )

        flight.longitude_deg = (
            longitude
            if longitude is not None
            else 0.0
        )

        flight.wind_speed_kt, flight.wind_direction_deg = wind_from_heading_track(
            tas_kt=flight.tas_kt,
            heading_deg=flight.heading_deg,
            ground_speed_kt=flight.ground_speed_kt,
            track_deg=flight.track_deg,
        )

        flight.turn_rate_deg_sec = raw.yaw_rate_deg_s
        flight.slip_skid = calculate_slip_skid(raw.accel_y_g, raw.accel_z_g)

        waypoint = self.get_selected_waypoint()
        active_leg = self.route_manager.get_active_leg()

        desired_track = raw.desired_track_deg or flight.track_deg

        if active_leg is not None:
            desired_track = active_leg.desired_track_deg
        if self.config.obs.enabled:
            desired_track = self.config.obs.selected_course_deg

        if flight.position_valid:
            nav = calculate_nav_solution(
                aircraft_lat_deg=flight.latitude_deg,
                aircraft_lon_deg=flight.longitude_deg,
                aircraft_alt_ft=flight.pressure_alt_ft,
                waypoint=waypoint,
                desired_track_deg=desired_track,
                glidepath_angle_deg=(
                    self.config.vnav.glidepath_angle_deg
                ),
                cdi_full_scale_nm=get_cdi_full_scale_nm(
                    self.config
                ),
                vnav_enabled=self.config.vnav.enabled,
            )

            flight.bearing_deg = nav.bearing_to_wp_deg
            flight.distance_to_waypoint_nm = (
                nav.distance_to_wp_nm
            )
            flight.course_error_deg = nav.course_error_deg
            flight.cdi = nav.cdi_deflection_nm
            flight.vdi = nav.vdi_deflection_deg
            flight.desired_track_deg = nav.desired_track_deg

        else:
            flight.bearing_deg = 0.0
            flight.distance_to_waypoint_nm = 0.0
            flight.course_error_deg = 0.0
            flight.cdi = 0.0
            flight.vdi = 0.0
            flight.desired_track_deg = desired_track

        if (
            flight.position_valid
            and self.config.route.auto_sequence
        ):
            self.route_manager.maybe_advance_leg(
                distance_to_waypoint_nm=nav.distance_to_wp_nm,
                sequence_distance_nm=(
                    self.config.route.sequence_distance_nm
                ),
            )
        else:
            flight.desired_track_deg = desired_track

        return flight

    def get_selected_waypoint(self) -> NavPoint:
        airport = self.database.get_airport(
            self.config.navigation.selected_waypoint_id
        )

        if airport is not None:
            return NavPoint(
                ident=airport.ident,
                name=airport.name,
                lat_deg=airport.lat_deg,
                lon_deg=airport.lon_deg,
                elevation_ft=airport.elevation_ft,
            )

        return NavPoint(
            ident=self.config.navigation.selected_waypoint_id,
            name=self.config.navigation.selected_waypoint_name,
            lat_deg=self.config.navigation.selected_waypoint_lat,
            lon_deg=self.config.navigation.selected_waypoint_lon,
            elevation_ft=0.0,
        )

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


def get_cdi_full_scale_nm(config) -> float:
    mode = config.navigation_scaling.mode.lower()

    if mode == "approach":
        return config.navigation_scaling.approach_full_scale_nm

    if mode == "terminal":
        return config.navigation_scaling.terminal_full_scale_nm

    return config.navigation_scaling.enroute_full_scale_nm


def calculate_slip_skid(accel_y_g: float, accel_z_g: float) -> float:
    if abs(accel_z_g) < 0.05:
        return 0.0

    slip = accel_y_g / abs(accel_z_g)
    return max(-1.0, min(1.0, slip))


def normalize_degrees(value: float) -> float:
    return value % 360.0

def safe_latitude(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not -90.0 <= number <= 90.0:
        return None

    return number


def safe_longitude(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not -180.0 <= number <= 180.0:
        return None

    return number