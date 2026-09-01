from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from pyefis.user.blake_pfd.core.terrain_awareness import (
    TerrainAwareness,
    TerrainProfilePoint,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
)


FEET_PER_NM = 6076.12

SEVERITY_ORDER = {
    "NONE": 0,
    "CAUTION": 1,
    "WARNING": 2,
    "CRITICAL": 3,
}


@dataclass(frozen=True)
class TerrainVisualTriangle:
    triangle_index: int
    warning_level: str = "NONE"


@dataclass(frozen=True)
class TerrainVisualClassification:
    triangles: tuple[
        TerrainVisualTriangle,
        ...,
    ] = ()

    valid: bool = False
    message: str = ""


class TerrainVisualClassifier:
    def __init__(
        self,
        awareness: TerrainAwareness | None = None,
    ) -> None:
        self.awareness = (
            awareness
            if awareness is not None
            else TerrainAwareness()
        )

    def classify(
        self,
        *,
        surface: TerrainSurface,
        aircraft_altitude_ft,
        vertical_speed_fpm=0.0,
        ground_speed_kt=0.0,
    ) -> TerrainVisualClassification:
        if not surface.valid:
            return TerrainVisualClassification(
                message="TERRAIN SURFACE INVALID",
            )

        vertex_count = len(
            surface.vertices
        )

        classified_triangles: list[
            TerrainVisualTriangle
        ] = []

        vertex_warning_levels: dict[
            int,
            str,
        ] = {}

        for (
            triangle_index,
            triangle,
        ) in enumerate(
            surface.triangles
        ):
            indices = (
                triangle.first_index,
                triangle.second_index,
                triangle.third_index,
            )

            if any(
                index < 0
                or index >= vertex_count
                for index in indices
            ):
                return TerrainVisualClassification(
                    message="TERRAIN TRIANGLE INVALID",
                )

            warning_level = "NONE"

            for index in indices:
                candidate = (
                    vertex_warning_levels.get(
                        index
                    )
                )

                if candidate is None:
                    vertex = surface.vertices[
                        index
                    ]

                    distance_nm = (
                        hypot(
                            vertex.north_ft,
                            vertex.east_ft,
                        )
                        / FEET_PER_NM
                    )

                    state = self.awareness.evaluate(
                        aircraft_altitude_ft=(
                            aircraft_altitude_ft
                        ),
                        vertical_speed_fpm=(
                            vertical_speed_fpm
                        ),
                        ground_speed_kt=(
                            ground_speed_kt
                        ),
                        profile=(
                            TerrainProfilePoint(
                                distance_nm=(
                                    distance_nm
                                ),
                                elevation_ft=(
                                    vertex.elevation_ft
                                ),
                            ),
                        ),
                    )

                    if not state.valid:
                        return TerrainVisualClassification(
                            message=(
                                "TERRAIN "
                                "CLASSIFICATION INVALID"
                            ),
                        )

                    candidate = (
                        state.warning_level
                    )

                    vertex_warning_levels[
                        index
                    ] = candidate

                if (
                    SEVERITY_ORDER[
                        candidate
                    ]
                    > SEVERITY_ORDER[
                        warning_level
                    ]
                ):
                    warning_level = (
                        candidate
                    )

            classified_triangles.append(
                TerrainVisualTriangle(
                    triangle_index=(
                        triangle_index
                    ),
                    warning_level=(
                        warning_level
                    ),
                )
            )

        return TerrainVisualClassification(
            triangles=tuple(
                classified_triangles
            ),
            valid=True,
        )
