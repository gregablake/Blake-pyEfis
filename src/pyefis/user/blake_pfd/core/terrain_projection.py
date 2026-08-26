from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.synthetic_camera import (
    ProjectedPoint,
    SyntheticCamera,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
)


@dataclass(frozen=True)
class ProjectedTerrainTriangle:
    first: ProjectedPoint
    second: ProjectedPoint
    third: ProjectedPoint

    elevations_ft: tuple[
        float,
        float,
        float,
    ]

    @property
    def visible(self) -> bool:
        return (
            self.first.visible
            and self.second.visible
            and self.third.visible
        )


@dataclass(frozen=True)
class ProjectedTerrain:
    triangles: tuple[
        ProjectedTerrainTriangle,
        ...,
    ] = ()

    valid: bool = False
    message: str = ""


class TerrainProjectionComputer:
    def __init__(
        self,
        camera: SyntheticCamera | None = None,
    ) -> None:
        self.camera = (
            camera
            if camera is not None
            else SyntheticCamera()
        )

    def project(
        self,
        *,
        surface: TerrainSurface,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
        width_px: int,
        height_px: int,
    ) -> ProjectedTerrain:
        if not surface.valid:
            return ProjectedTerrain(
                message="TERRAIN SURFACE INVALID",
            )

        projected_triangles: list[
            ProjectedTerrainTriangle
        ] = []

        vertex_count = len(
            surface.vertices
        )

        for triangle in surface.triangles:
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
                return ProjectedTerrain(
                    message="TERRAIN TRIANGLE INVALID",
                )

            first_vertex = surface.vertices[
                triangle.first_index
            ]

            second_vertex = surface.vertices[
                triangle.second_index
            ]

            third_vertex = surface.vertices[
                triangle.third_index
            ]

            first = self._project_vertex(
                vertex=first_vertex,
                heading_deg=heading_deg,
                pitch_deg=pitch_deg,
                roll_deg=roll_deg,
                width_px=width_px,
                height_px=height_px,
            )

            second = self._project_vertex(
                vertex=second_vertex,
                heading_deg=heading_deg,
                pitch_deg=pitch_deg,
                roll_deg=roll_deg,
                width_px=width_px,
                height_px=height_px,
            )

            third = self._project_vertex(
                vertex=third_vertex,
                heading_deg=heading_deg,
                pitch_deg=pitch_deg,
                roll_deg=roll_deg,
                width_px=width_px,
                height_px=height_px,
            )

            if (
                first is None
                or second is None
                or third is None
            ):
                return ProjectedTerrain(
                    message=(
                        "TERRAIN PROJECTION INVALID"
                    ),
                )

            projected_triangles.append(
                ProjectedTerrainTriangle(
                    first=first,
                    second=second,
                    third=third,
                    elevations_ft=(
                        first_vertex.elevation_ft,
                        second_vertex.elevation_ft,
                        third_vertex.elevation_ft,
                    ),
                )
            )

        return ProjectedTerrain(
            triangles=tuple(
                projected_triangles
            ),
            valid=True,
        )

    def _project_vertex(
        self,
        *,
        vertex,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
        width_px: int,
        height_px: int,
    ) -> ProjectedPoint | None:
        camera_point = (
            self.camera.world_to_camera(
                north_ft=vertex.north_ft,
                east_ft=vertex.east_ft,
                up_ft=vertex.up_ft,
                heading_deg=heading_deg,
                pitch_deg=pitch_deg,
                roll_deg=roll_deg,
            )
        )

        if camera_point is None:
            return None

        return self.camera.project(
            camera_point,
            width_px=width_px,
            height_px=height_px,
        )
