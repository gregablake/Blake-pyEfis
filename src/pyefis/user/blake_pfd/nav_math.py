from __future__ import annotations

from dataclasses import dataclass
from math import atan2, asin, cos, degrees, radians, sin


EARTH_RADIUS_NM = 3440.065


@dataclass
class NavPoint:
    ident: str
    name: str
    lat_deg: float
    lon_deg: float
    elevation_ft: float = 0.0


@dataclass
class NavSolution:
    bearing_to_wp_deg: float = 0.0
    distance_to_wp_nm: float = 0.0
    desired_track_deg: float = 0.0
    cdi_deflection_nm: float = 0.0
    cdi_percent: float = 0.0
    vdi_deflection_deg: float = 0.0
    course_error_deg: float = 0.0
    glidepath_target_alt_ft: float = 0.0
    glidepath_alt_error_ft: float = 0.0

def calculate_nav_solution(
    aircraft_lat_deg: float,
    aircraft_lon_deg: float,
    aircraft_alt_ft: float,
    waypoint: NavPoint,
    desired_track_deg: float,
    glidepath_angle_deg: float = 3.0,
    cdi_full_scale_nm: float = 1.0,
    vnav_enabled: bool = True,
) -> NavSolution:
    bearing = bearing_between_points_deg(
        aircraft_lat_deg,
        aircraft_lon_deg,
        waypoint.lat_deg,
        waypoint.lon_deg,
    )

    distance_nm = distance_between_points_nm(
        aircraft_lat_deg,
        aircraft_lon_deg,
        waypoint.lat_deg,
        waypoint.lon_deg,
    )

    cross_track_nm = calculate_cross_track_error_nm(
        aircraft_lat_deg,
        aircraft_lon_deg,
        waypoint.lat_deg,
        waypoint.lon_deg,
        desired_track_deg,
    )

    cdi_percent = clamp(cross_track_nm / cdi_full_scale_nm, -1.0, 1.0)

    if vnav_enabled:
        target_alt_ft = calculate_glidepath_altitude_ft(
            distance_nm,
            waypoint.elevation_ft,
            glidepath_angle_deg,
        )
        altitude_error_ft = aircraft_alt_ft - target_alt_ft
        vdi_deflection_deg = clamp(altitude_error_ft / 300.0, -1.0, 1.0)
    else:
        target_alt_ft = 0.0
        altitude_error_ft = 0.0
        vdi_deflection_deg = 0.0

    course_error_deg = angle_delta_deg(bearing, desired_track_deg)

    return NavSolution(
        bearing_to_wp_deg=bearing,
        distance_to_wp_nm=distance_nm,
        desired_track_deg=normalize_degrees(desired_track_deg),
        cdi_deflection_nm=cross_track_nm,
        cdi_percent=cdi_percent,
        vdi_deflection_deg=vdi_deflection_deg,
        course_error_deg=course_error_deg,
        glidepath_target_alt_ft=target_alt_ft,
        glidepath_alt_error_ft=altitude_error_ft,
    )

def bearing_between_points_deg(
    lat1_deg: float,
    lon1_deg: float,
    lat2_deg: float,
    lon2_deg: float,
) -> float:
    lat1 = radians(lat1_deg)
    lat2 = radians(lat2_deg)
    dlon = radians(lon2_deg - lon1_deg)

    x = sin(dlon) * cos(lat2)
    y = (cos(lat1) * sin(lat2)) - (sin(lat1) * cos(lat2) * cos(dlon))

    return normalize_degrees(degrees(atan2(x, y)))


def distance_between_points_nm(
    lat1_deg: float,
    lon1_deg: float,
    lat2_deg: float,
    lon2_deg: float,
) -> float:
    lat1 = radians(lat1_deg)
    lat2 = radians(lat2_deg)
    dlat = radians(lat2_deg - lat1_deg)
    dlon = radians(lon2_deg - lon1_deg)

    a = (
        sin(dlat / 2.0) ** 2
        + cos(lat1) * cos(lat2) * (sin(dlon / 2.0) ** 2)
    )

    c = 2.0 * atan2(a ** 0.5, (1.0 - a) ** 0.5)

    return EARTH_RADIUS_NM * c


def calculate_cross_track_error_nm(
    aircraft_lat_deg: float,
    aircraft_lon_deg: float,
    waypoint_lat_deg: float,
    waypoint_lon_deg: float,
    desired_track_deg: float,
) -> float:
    distance_to_wp_nm = distance_between_points_nm(
        aircraft_lat_deg,
        aircraft_lon_deg,
        waypoint_lat_deg,
        waypoint_lon_deg,
    )

    bearing_to_wp_deg = bearing_between_points_deg(
        aircraft_lat_deg,
        aircraft_lon_deg,
        waypoint_lat_deg,
        waypoint_lon_deg,
    )

    angle_error_rad = radians(angle_delta_deg(bearing_to_wp_deg, desired_track_deg))

    return distance_to_wp_nm * sin(angle_error_rad)


def calculate_glidepath_altitude_ft(
    distance_to_wp_nm: float,
    waypoint_elevation_ft: float,
    glidepath_angle_deg: float,
) -> float:
    feet_per_nm = 6076.12
    glidepath_rad = radians(glidepath_angle_deg)
    height_above_wp_ft = distance_to_wp_nm * feet_per_nm * sin(glidepath_rad)

    return waypoint_elevation_ft + height_above_wp_ft


def angle_delta_deg(new_angle: float, old_angle: float) -> float:
    return (new_angle - old_angle + 180.0) % 360.0 - 180.0


def normalize_degrees(value: float) -> float:
    return value % 360.0


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))