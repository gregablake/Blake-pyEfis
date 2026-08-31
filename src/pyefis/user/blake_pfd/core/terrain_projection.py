from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.synthetic_camera import (
    CameraPoint,
    ProjectedPoint,
    SyntheticCamera,
)
from pyefis.user.blake_pfd.core.synthetic_clipping import (
    clip_camera_polygon_to_near_plane,
    clip_projected_polygon_to_screen,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
)


@dataclass(frozen=True)
class ProjectedTerrainTriangle:
    points: tuple[
        ProjectedPoint,
        ...,
    ] = ()

    elevations_ft: tuple[
        float,
        float,
        float,
    ] = (
        0.0,
        0.0,
        0.0,
    )

    @property
    def visible(self) -> bool:
        return len(self.points) >= 3

    @property
    def first(self) -> ProjectedPoint:
        return self._point_or_hidden(0)

    @property
    def second(self) -> ProjectedPoint:
        return self._point_or_hidden(1)

    @property
    def third(self) -> ProjectedPoint:
        return self._point_or_hidden(2)

    def _point_or_hidden(
        self,
        index: int,
    ) -> ProjectedPoint:
        if index < len(self.points):
            return self.points[index]

        return ProjectedPoint(
            x_px=0.0,
            y_px=0.0,
            visible=False,
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
        *,
        near_plane_ft: float = 5.0,
    ) -> None:
        self.camera = (
            camera
            if camera is not None
            else SyntheticCamera()
        )

        self.near_plane_ft = float(
            near_plane_ft
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

        if (
            width_px <= 0
            or height_px <= 0
            or self.near_plane_ft <= 0.0
        ):
            return ProjectedTerrain(
                message=(
                    "TERRAIN PROJECTION INVALID"
                ),
            )

        projected_triangles: list[
            ProjectedTerrainTriangle
        ] = []

        vertex_count = len(
            surface.vertices
        )

        camera_point_cache: dict[
            int,
            CameraPoint,
        ] = {}

        projected_point_cache: dict[
            int,
            ProjectedPoint,
        ] = {}

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

            source_vertices = tuple(
                surface.vertices[index]
                for index in indices
            )

            camera_points: list[
                CameraPoint
            ] = []

            for index, vertex in zip(
                indices,
                source_vertices,
            ):
                camera_point = (
                    camera_point_cache.get(
                        index
                    )
                )

                if camera_point is None:
                    camera_point = (
                        self.camera.world_to_camera(
                            north_ft=(
                                vertex.north_ft
                            ),
                            east_ft=(
                                vertex.east_ft
                            ),
                            up_ft=(
                                vertex.up_ft
                            ),
                            heading_deg=heading_deg,
                            pitch_deg=pitch_deg,
                            roll_deg=roll_deg,
                        )
                    )

                    if camera_point is None:
                        return ProjectedTerrain(
                            message=(
                                "TERRAIN "
                                "PROJECTION INVALID"
                            ),
                        )

                    camera_point_cache[
                        index
                    ] = camera_point

                camera_points.append(
                    camera_point
                )

            source_camera_points = tuple(
                camera_points
            )

            all_points_in_front = all(
                point.forward_ft >= self.near_plane_ft
                for point in source_camera_points
            )

            if all_points_in_front:
                clipped_camera_points = (
                    source_camera_points
                )
            else:
                clipped_camera_points = (
                    clip_camera_polygon_to_near_plane(
                        source_camera_points,
                        near_plane_ft=(
                            self.near_plane_ft
                        ),
                    )
                )

            if not clipped_camera_points:
                projected_triangles.append(
                    ProjectedTerrainTriangle(
                        elevations_ft=tuple(
                            vertex.elevation_ft
                            for vertex
                            in source_vertices
                        ),
                    )
                )

                continue

            projected_points: list[
                ProjectedPoint
            ] = []

            polygon_was_not_near_clipped = (
                all_points_in_front
            )

            if polygon_was_not_near_clipped:
                for index, camera_point in zip(
                    indices,
                    source_camera_points,
                ):
                    projected_point = (
                        projected_point_cache.get(
                            index
                        )
                    )

                    if projected_point is None:
                        projected_point = (
                            self.camera.project(
                                camera_point,
                                width_px=width_px,
                                height_px=height_px,
                                near_plane_ft=(
                                    self.near_plane_ft
                                ),
                            )
                        )

                        if projected_point is None:
                            return ProjectedTerrain(
                                message=(
                                    "TERRAIN "
                                    "PROJECTION INVALID"
                                ),
                            )

                        projected_point_cache[
                            index
                        ] = projected_point

                    projected_points.append(
                        projected_point
                    )

            else:
                # Near-plane clipping may create new
                # intersection vertices that do not
                # correspond to source mesh indices.
                for camera_point in (
                    clipped_camera_points
                ):
                    projected_point = (
                        self.camera.project(
                            camera_point,
                            width_px=width_px,
                            height_px=height_px,
                            near_plane_ft=(
                                self.near_plane_ft
                            ),
                        )
                    )

                    if projected_point is None:
                        return ProjectedTerrain(
                            message=(
                                "TERRAIN "
                                "PROJECTION INVALID"
                            ),
                        )

                    projected_points.append(
                        projected_point
                    )

            source_projected_points = tuple(
                projected_points
            )

            all_points_onscreen = all(
                point.visible
                for point in source_projected_points
            )

            if all_points_onscreen:
                clipped_screen_points = (
                    source_projected_points
                )
            else:
                clipped_screen_points = (
                    clip_projected_polygon_to_screen(
                        source_projected_points,
                        width_px=width_px,
                        height_px=height_px,
                    )
                )

            projected_triangles.append(
                ProjectedTerrainTriangle(
                    points=(
                        clipped_screen_points
                    ),
                    elevations_ft=tuple(
                        vertex.elevation_ft
                        for vertex
                        in source_vertices
                    ),
                )
            )

        return ProjectedTerrain(
            triangles=tuple(
                projected_triangles
            ),
            valid=True,
        )
