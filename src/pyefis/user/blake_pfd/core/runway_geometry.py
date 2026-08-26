from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, radians, sin

from pyefis.user.blake_pfd.nav_math import (
    bearing_between_points_deg,
    distance_between_points_nm,
)


FEET_PER_NM = 6076.12


@dataclass(frozen=True)
class RunwayEndpointGeometry:
    ident: str
    north_ft: float
    east_ft: float
    up_ft: float
    distance_ft: float
    bearing_deg: float
    elevation_ft: float


@dataclass(frozen=True)
class RunwayGeometry:
    airport_ident: str
    length_ft: float
    width_ft: float
    low_end: RunwayEndpointGeometry
    high_end: RunwayEndpointGeometry


class RunwayGeometryComputer:
    def compute(
        self,
        runway,
        aircraft_lat_deg: float,
        aircraft_lon_deg: float,
        aircraft_alt_ft: float,
    ) -> RunwayGeometry | None:
        if not self._valid_aircraft_position(
            aircraft_lat_deg,
            aircraft_lon_deg,
            aircraft_alt_ft,
        ):
            return None

        low_end = self._endpoint_geometry(
            ident=runway.le_ident,
            latitude_deg=runway.le_latitude_deg,
            longitude_deg=runway.le_longitude_deg,
            elevation_ft=runway.le_elevation_ft,
            aircraft_lat_deg=aircraft_lat_deg,
            aircraft_lon_deg=aircraft_lon_deg,
            aircraft_alt_ft=aircraft_alt_ft,
        )

        high_end = self._endpoint_geometry(
            ident=runway.he_ident,
            latitude_deg=runway.he_latitude_deg,
            longitude_deg=runway.he_longitude_deg,
            elevation_ft=runway.he_elevation_ft,
            aircraft_lat_deg=aircraft_lat_deg,
            aircraft_lon_deg=aircraft_lon_deg,
            aircraft_alt_ft=aircraft_alt_ft,
        )

        if low_end is None or high_end is None:
            return None

        return RunwayGeometry(
            airport_ident=runway.airport_ident,
            length_ft=float(runway.length_ft),
            width_ft=float(runway.width_ft),
            low_end=low_end,
            high_end=high_end,
        )

    def _endpoint_geometry(
        self,
        ident: str,
        latitude_deg: float | None,
        longitude_deg: float | None,
        elevation_ft: float | None,
        aircraft_lat_deg: float,
        aircraft_lon_deg: float,
        aircraft_alt_ft: float,
    ) -> RunwayEndpointGeometry | None:
        if (
            latitude_deg is None
            or longitude_deg is None
            or elevation_ft is None
        ):
            return None

        if not self._valid_lat_lon(
            latitude_deg,
            longitude_deg,
        ):
            return None

        if not isfinite(elevation_ft):
            return None

        distance_nm = distance_between_points_nm(
            aircraft_lat_deg,
            aircraft_lon_deg,
            latitude_deg,
            longitude_deg,
        )

        bearing_deg = bearing_between_points_deg(
            aircraft_lat_deg,
            aircraft_lon_deg,
            latitude_deg,
            longitude_deg,
        )

        distance_ft = distance_nm * FEET_PER_NM
        bearing_rad = radians(bearing_deg)

        north_ft = distance_ft * cos(bearing_rad)
        east_ft = distance_ft * sin(bearing_rad)

        up_ft = elevation_ft - aircraft_alt_ft

        return RunwayEndpointGeometry(
            ident=ident,
            north_ft=north_ft,
            east_ft=east_ft,
            up_ft=up_ft,
            distance_ft=distance_ft,
            bearing_deg=bearing_deg,
            elevation_ft=elevation_ft,
        )

    @staticmethod
    def _valid_lat_lon(
        latitude_deg: float,
        longitude_deg: float,
    ) -> bool:
        return (
            isfinite(latitude_deg)
            and isfinite(longitude_deg)
            and -90.0 <= latitude_deg <= 90.0
            and -180.0 <= longitude_deg <= 180.0
        )

    @classmethod
    def _valid_aircraft_position(
        cls,
        latitude_deg: float,
        longitude_deg: float,
        altitude_ft: float,
    ) -> bool:
        return (
            cls._valid_lat_lon(
                latitude_deg,
                longitude_deg,
            )
            and isfinite(altitude_ft)
        )
