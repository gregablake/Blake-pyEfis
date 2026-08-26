from __future__ import annotations

from math import (
    cos,
    isfinite,
    radians,
    sin,
)

from pyefis.user.blake_pfd.nav_math import (
    bearing_between_points_deg,
    distance_between_points_nm,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    FEET_PER_NM,
    TerrainSurface,
    TerrainSurfaceVertex,
)


class TerrainSurfaceRebaser:
    def rebase(
        self,
        *,
        surface: TerrainSurface,
        aircraft_lat_deg,
        aircraft_lon_deg,
        aircraft_alt_ft,
    ) -> TerrainSurface:
        if not surface.valid:
            return TerrainSurface(
                message="TERRAIN SURFACE INVALID",
            )

        latitude = self._safe_latitude(
            aircraft_lat_deg
        )
        longitude = self._safe_longitude(
            aircraft_lon_deg
        )
        altitude = self._safe_number(
            aircraft_alt_ft
        )

        if (
            latitude is None
            or longitude is None
            or altitude is None
        ):
            return TerrainSurface(
                message="AIRCRAFT POSITION INVALID",
            )

        rebased_vertices: list[
            TerrainSurfaceVertex
        ] = []

        for vertex in surface.vertices:
            vertex_latitude = self._safe_latitude(
                vertex.latitude_deg
            )
            vertex_longitude = self._safe_longitude(
                vertex.longitude_deg
            )
            elevation = self._safe_number(
                vertex.elevation_ft
            )

            if (
                vertex_latitude is None
                or vertex_longitude is None
                or elevation is None
            ):
                return TerrainSurface(
                    message=(
                        "TERRAIN VERTEX INVALID"
                    ),
                )

            distance_nm = (
                distance_between_points_nm(
                    latitude,
                    longitude,
                    vertex_latitude,
                    vertex_longitude,
                )
            )

            bearing_deg = (
                bearing_between_points_deg(
                    latitude,
                    longitude,
                    vertex_latitude,
                    vertex_longitude,
                )
            )

            if not (
                isfinite(distance_nm)
                and isfinite(bearing_deg)
            ):
                return TerrainSurface(
                    message=(
                        "TERRAIN REBASE INVALID"
                    ),
                )

            distance_ft = (
                distance_nm
                * FEET_PER_NM
            )

            bearing_rad = radians(
                bearing_deg
            )

            north_ft = (
                distance_ft
                * cos(bearing_rad)
            )

            east_ft = (
                distance_ft
                * sin(bearing_rad)
            )

            up_ft = (
                elevation
                - altitude
            )

            if not all(
                isfinite(value)
                for value in (
                    north_ft,
                    east_ft,
                    up_ft,
                )
            ):
                return TerrainSurface(
                    message=(
                        "TERRAIN REBASE INVALID"
                    ),
                )

            rebased_vertices.append(
                TerrainSurfaceVertex(
                    north_ft=north_ft,
                    east_ft=east_ft,
                    up_ft=up_ft,
                    latitude_deg=(
                        vertex_latitude
                    ),
                    longitude_deg=(
                        vertex_longitude
                    ),
                    elevation_ft=elevation,
                )
            )

        return TerrainSurface(
            vertices=tuple(
                rebased_vertices
            ),
            triangles=surface.triangles,
            rows=surface.rows,
            columns=surface.columns,
            valid=True,
        )

    @staticmethod
    def _safe_number(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return number

    @classmethod
    def _safe_latitude(
        cls,
        value,
    ) -> float | None:
        latitude = cls._safe_number(
            value
        )

        if (
            latitude is None
            or latitude < -90.0
            or latitude > 90.0
        ):
            return None

        return latitude

    @classmethod
    def _safe_longitude(
        cls,
        value,
    ) -> float | None:
        longitude = cls._safe_number(
            value
        )

        if (
            longitude is None
            or longitude < -180.0
            or longitude > 180.0
        ):
            return None

        return longitude
