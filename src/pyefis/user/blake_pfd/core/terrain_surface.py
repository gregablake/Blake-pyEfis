from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import (
    asin,
    atan2,
    cos,
    degrees,
    hypot,
    isfinite,
    radians,
    sin,
)


EARTH_RADIUS_NM = 3440.065
FEET_PER_NM = 6076.12


@dataclass(frozen=True)
class TerrainSurfaceVertex:
    north_ft: float
    east_ft: float
    up_ft: float

    latitude_deg: float
    longitude_deg: float
    elevation_ft: float


@dataclass(frozen=True)
class TerrainTriangle:
    first_index: int
    second_index: int
    third_index: int


@dataclass(frozen=True)
class TerrainSurface:
    vertices: tuple[
        TerrainSurfaceVertex,
        ...,
    ] = ()

    triangles: tuple[
        TerrainTriangle,
        ...,
    ] = ()

    rows: int = 0
    columns: int = 0

    valid: bool = False
    message: str = ""


class TerrainSurfaceGenerator:
    def __init__(
        self,
        *,
        elevation_sampler: Callable[
            [float, float],
            float | None,
        ],
        forward_distances_nm: tuple[
            float,
            ...,
        ] = (
            0.5,
            1.0,
            2.0,
            3.0,
            5.0,
            8.0,
            10.0,
        ),
        lateral_fractions: tuple[
            float,
            ...,
        ] = (
            -1.0,
            -0.5,
            0.0,
            0.5,
            1.0,
        ),
        half_width_ratio: float = 0.5,
    ) -> None:
        if not callable(elevation_sampler):
            raise TypeError(
                "elevation_sampler must be callable"
            )

        self.elevation_sampler = (
            elevation_sampler
        )

        self.forward_distances_nm = (
            self._validate_forward_distances(
                forward_distances_nm
            )
        )

        self.lateral_fractions = (
            self._validate_lateral_fractions(
                lateral_fractions
            )
        )

        try:
            width_ratio = float(
                half_width_ratio
            )
        except (TypeError, ValueError):
            raise ValueError(
                "half_width_ratio must be numeric"
            ) from None

        if (
            not isfinite(width_ratio)
            or width_ratio <= 0.0
        ):
            raise ValueError(
                "half_width_ratio must be finite "
                "and positive"
            )

        self.half_width_ratio = (
            width_ratio
        )

    def generate(
        self,
        *,
        aircraft_lat_deg,
        aircraft_lon_deg,
        aircraft_alt_ft,
        heading_deg,
    ) -> TerrainSurface:
        latitude = self._safe_latitude(
            aircraft_lat_deg
        )

        longitude = self._safe_longitude(
            aircraft_lon_deg
        )

        altitude = self._safe_number(
            aircraft_alt_ft
        )

        heading = self._safe_number(
            heading_deg
        )

        if (
            latitude is None
            or longitude is None
            or altitude is None
            or heading is None
        ):
            return TerrainSurface(
                message=(
                    "AIRCRAFT POSITION INVALID"
                ),
            )

        heading = heading % 360.0
        heading_rad = radians(
            heading
        )

        rows = len(
            self.forward_distances_nm
        )

        columns = len(
            self.lateral_fractions
        )

        grid_vertices: list[
            TerrainSurfaceVertex | None
        ] = []

        missing_sample = False

        for (
            forward_distance_nm
        ) in self.forward_distances_nm:
            forward_ft = (
                forward_distance_nm
                * FEET_PER_NM
            )

            half_width_ft = (
                forward_ft
                * self.half_width_ratio
            )

            for (
                lateral_fraction
            ) in self.lateral_fractions:
                lateral_ft = (
                    lateral_fraction
                    * half_width_ft
                )

                north_ft = (
                    forward_ft
                    * cos(heading_rad)
                    - lateral_ft
                    * sin(heading_rad)
                )

                east_ft = (
                    forward_ft
                    * sin(heading_rad)
                    + lateral_ft
                    * cos(heading_rad)
                )

                sample_distance_nm = (
                    hypot(
                        north_ft,
                        east_ft,
                    )
                    / FEET_PER_NM
                )

                sample_bearing_deg = (
                    degrees(
                        atan2(
                            east_ft,
                            north_ft,
                        )
                    )
                    % 360.0
                )

                (
                    sample_latitude,
                    sample_longitude,
                ) = self._destination_point(
                    latitude_deg=latitude,
                    longitude_deg=longitude,
                    bearing_deg=(
                        sample_bearing_deg
                    ),
                    distance_nm=(
                        sample_distance_nm
                    ),
                )

                elevation = (
                    self._safe_number(
                        self.elevation_sampler(
                            sample_latitude,
                            sample_longitude,
                        )
                    )
                )

                if elevation is None:
                    missing_sample = True
                    grid_vertices.append(
                        None
                    )
                    continue

                grid_vertices.append(
                    TerrainSurfaceVertex(
                        north_ft=north_ft,
                        east_ft=east_ft,
                        up_ft=(
                            elevation
                            - altitude
                        ),
                        latitude_deg=(
                            sample_latitude
                        ),
                        longitude_deg=(
                            sample_longitude
                        ),
                        elevation_ft=(
                            elevation
                        ),
                    )
                )

        source_triangles: list[
            tuple[int, int, int]
        ] = []

        for row in range(
            rows - 1
        ):
            for column in range(
                columns - 1
            ):
                near_left = (
                    row * columns
                    + column
                )

                near_right = (
                    near_left + 1
                )

                far_left = (
                    (row + 1)
                    * columns
                    + column
                )

                far_right = (
                    far_left + 1
                )

                cell_indices = (
                    near_left,
                    near_right,
                    far_left,
                    far_right,
                )

                if any(
                    grid_vertices[index]
                    is None
                    for index in cell_indices
                ):
                    continue

                source_triangles.append(
                    (
                        near_left,
                        far_left,
                        far_right,
                    )
                )

                source_triangles.append(
                    (
                        near_left,
                        far_right,
                        near_right,
                    )
                )

        if not source_triangles:
            return TerrainSurface(
                message=(
                    "TERRAIN SAMPLE "
                    "UNAVAILABLE"
                ),
            )

        used_indices = sorted(
            {
                index
                for triangle
                in source_triangles
                for index in triangle
            }
        )

        index_map = {
            source_index: compact_index
            for compact_index, source_index
            in enumerate(used_indices)
        }

        vertices: list[
            TerrainSurfaceVertex
        ] = []

        for source_index in used_indices:
            vertex = grid_vertices[
                source_index
            ]

            if vertex is None:
                return TerrainSurface(
                    message=(
                        "TERRAIN SAMPLE "
                        "UNAVAILABLE"
                    ),
                )

            vertices.append(
                vertex
            )

        triangles = tuple(
            TerrainTriangle(
                first_index=index_map[
                    first_index
                ],
                second_index=index_map[
                    second_index
                ],
                third_index=index_map[
                    third_index
                ],
            )
            for (
                first_index,
                second_index,
                third_index,
            ) in source_triangles
        )

        return TerrainSurface(
            vertices=tuple(vertices),
            triangles=triangles,
            rows=rows,
            columns=columns,
            valid=True,
            message=(
                "TERRAIN PARTIAL"
                if missing_sample
                else ""
            ),
        )

    @staticmethod
    def _destination_point(
        *,
        latitude_deg: float,
        longitude_deg: float,
        bearing_deg: float,
        distance_nm: float,
    ) -> tuple[float, float]:
        latitude_rad = radians(
            latitude_deg
        )

        longitude_rad = radians(
            longitude_deg
        )

        bearing_rad = radians(
            bearing_deg
        )

        angular_distance = (
            distance_nm
            / EARTH_RADIUS_NM
        )

        destination_latitude_rad = (
            asin(
                sin(latitude_rad)
                * cos(angular_distance)
                + cos(latitude_rad)
                * sin(angular_distance)
                * cos(bearing_rad)
            )
        )

        destination_longitude_rad = (
            longitude_rad
            + atan2(
                sin(bearing_rad)
                * sin(angular_distance)
                * cos(latitude_rad),
                cos(angular_distance)
                - sin(latitude_rad)
                * sin(
                    destination_latitude_rad
                ),
            )
        )

        destination_latitude_deg = (
            degrees(
                destination_latitude_rad
            )
        )

        destination_longitude_deg = (
            (
                degrees(
                    destination_longitude_rad
                )
                + 540.0
            )
            % 360.0
            - 180.0
        )

        return (
            destination_latitude_deg,
            destination_longitude_deg,
        )

    @staticmethod
    def _validate_forward_distances(
        values,
    ) -> tuple[float, ...]:
        try:
            distances = tuple(
                float(value)
                for value in values
            )
        except (TypeError, ValueError):
            raise ValueError(
                "forward distances must be "
                "numeric"
            ) from None

        if len(distances) < 2:
            raise ValueError(
                "at least two forward "
                "distances are required"
            )

        previous = 0.0

        for distance in distances:
            if (
                not isfinite(distance)
                or distance <= 0.0
            ):
                raise ValueError(
                    "forward distances must "
                    "be finite and positive"
                )

            if distance <= previous:
                raise ValueError(
                    "forward distances must "
                    "be strictly increasing"
                )

            previous = distance

        return distances

    @staticmethod
    def _validate_lateral_fractions(
        values,
    ) -> tuple[float, ...]:
        try:
            fractions = tuple(
                float(value)
                for value in values
            )
        except (TypeError, ValueError):
            raise ValueError(
                "lateral fractions must be "
                "numeric"
            ) from None

        if len(fractions) < 2:
            raise ValueError(
                "at least two lateral "
                "fractions are required"
            )

        previous: float | None = None

        for fraction in fractions:
            if not isfinite(fraction):
                raise ValueError(
                    "lateral fractions must "
                    "be finite"
                )

            if (
                previous is not None
                and fraction <= previous
            ):
                raise ValueError(
                    "lateral fractions must "
                    "be strictly increasing"
                )

            previous = fraction

        return fractions

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

    @staticmethod
    def _safe_latitude(
        value,
    ) -> float | None:
        latitude = (
            TerrainSurfaceGenerator
            ._safe_number(value)
        )

        if (
            latitude is None
            or latitude < -90.0
            or latitude > 90.0
        ):
            return None

        return latitude

    @staticmethod
    def _safe_longitude(
        value,
    ) -> float | None:
        longitude = (
            TerrainSurfaceGenerator
            ._safe_number(value)
        )

        if (
            longitude is None
            or longitude < -180.0
            or longitude > 180.0
        ):
            return None

        return longitude
