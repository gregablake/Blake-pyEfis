from __future__ import annotations

from dataclasses import dataclass
from math import (
    atan2,
    cos,
    degrees,
    isfinite,
    radians,
    sin,
    sqrt,
)


EARTH_RADIUS_NM = 3440.065


@dataclass(frozen=True)
class TrafficGeometry:
    distance_nm: float
    bearing_deg: float
    relative_alt_ft: float | None


def _finite_number(
    value,
) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not isfinite(number):
        return None

    return number


def calculate_traffic_geometry(
    *,
    own_lat_deg,
    own_lon_deg,
    own_pressure_alt_ft,
    target_lat_deg,
    target_lon_deg,
    target_pressure_alt_ft,
) -> TrafficGeometry | None:
    """
    Calculate relative target geometry.

    Horizontal geometry comes from GPS position.

    Vertical separation intentionally compares
    pressure altitude to pressure altitude because
    GDL90 traffic altitude is pressure altitude.
    """

    own_lat = _finite_number(
        own_lat_deg
    )
    own_lon = _finite_number(
        own_lon_deg
    )

    target_lat = _finite_number(
        target_lat_deg
    )
    target_lon = _finite_number(
        target_lon_deg
    )

    if (
        own_lat is None
        or own_lon is None
        or target_lat is None
        or target_lon is None
    ):
        return None

    if not (
        -90.0 <= own_lat <= 90.0
        and -90.0 <= target_lat <= 90.0
        and -180.0 <= own_lon <= 180.0
        and -180.0 <= target_lon <= 180.0
    ):
        return None

    lat1 = radians(
        own_lat
    )
    lat2 = radians(
        target_lat
    )

    delta_lat = radians(
        target_lat - own_lat
    )

    delta_lon = radians(
        target_lon - own_lon
    )

    sin_half_lat = sin(
        delta_lat / 2.0
    )

    sin_half_lon = sin(
        delta_lon / 2.0
    )

    haversine = (
        sin_half_lat * sin_half_lat
        + cos(lat1)
        * cos(lat2)
        * sin_half_lon
        * sin_half_lon
    )

    haversine = max(
        0.0,
        min(
            1.0,
            haversine,
        ),
    )

    central_angle = (
        2.0
        * atan2(
            sqrt(haversine),
            sqrt(
                max(
                    0.0,
                    1.0 - haversine,
                )
            ),
        )
    )

    distance_nm = (
        EARTH_RADIUS_NM
        * central_angle
    )

    y = (
        sin(delta_lon)
        * cos(lat2)
    )

    x = (
        cos(lat1)
        * sin(lat2)
        - sin(lat1)
        * cos(lat2)
        * cos(delta_lon)
    )

    if distance_nm < 1e-9:
        bearing_deg = 0.0
    else:
        bearing_deg = (
            degrees(
                atan2(
                    y,
                    x,
                )
            )
            + 360.0
        ) % 360.0

    own_alt = _finite_number(
        own_pressure_alt_ft
    )

    target_alt = _finite_number(
        target_pressure_alt_ft
    )

    if (
        own_alt is None
        or target_alt is None
    ):
        relative_alt_ft = None
    else:
        relative_alt_ft = (
            target_alt
            - own_alt
        )

    return TrafficGeometry(
        distance_nm=distance_nm,
        bearing_deg=bearing_deg,
        relative_alt_ft=relative_alt_ft,
    )
