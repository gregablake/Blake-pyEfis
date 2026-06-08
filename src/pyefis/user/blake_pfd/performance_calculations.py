from __future__ import annotations

from math import atan2, cos, degrees, radians, sin, sqrt


def true_airspeed_estimate(
    ias_kt: float,
    pressure_alt_ft: float,
    oat_c: float,
) -> float:
    """
    Simple TAS estimate.
    Roughly 2% increase per 1,000 ft, corrected slightly for OAT.
    """

    altitude_factor = 1.0 + (0.02 * (pressure_alt_ft / 1000.0))
    temp_factor = 1.0 + ((oat_c - 15.0) * 0.001)

    return ias_kt * altitude_factor * temp_factor


def density_altitude_estimate(
    pressure_alt_ft: float,
    oat_c: float,
) -> float:
    """
    Density altitude estimate.
    """

    isa_temp_c = 15.0 - (1.98 * (pressure_alt_ft / 1000.0))
    return pressure_alt_ft + (120.0 * (oat_c - isa_temp_c))


def wind_from_heading_track(
    tas_kt: float,
    heading_deg: float,
    ground_speed_kt: float,
    track_deg: float,
) -> tuple[float, float]:
    """
    Estimate wind from air vector and GPS ground vector.

    Returns:
        wind_speed_kt, wind_from_direction_deg
    """

    heading_rad = radians(heading_deg)
    track_rad = radians(track_deg)

    air_north = tas_kt * cos(heading_rad)
    air_east = tas_kt * sin(heading_rad)

    ground_north = ground_speed_kt * cos(track_rad)
    ground_east = ground_speed_kt * sin(track_rad)

    wind_north = ground_north - air_north
    wind_east = ground_east - air_east

    wind_speed_kt = sqrt((wind_north ** 2) + (wind_east ** 2))

    wind_to_deg = degrees(atan2(wind_east, wind_north))
    wind_from_deg = normalize_degrees(wind_to_deg + 180.0)

    return wind_speed_kt, wind_from_deg


def normalize_degrees(value: float) -> float:
    return value % 360.0