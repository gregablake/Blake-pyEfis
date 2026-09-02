from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite

from pyefis.user.blake_pfd.core.runway_geometry import (
    RunwayGeometry,
)
from pyefis.user.blake_pfd.core.synthetic_camera import (
    CameraPoint,
    ProjectedPoint,
    SyntheticCamera,
)
from pyefis.user.blake_pfd.core.synthetic_clipping import (
    clip_camera_polygon_to_near_plane,
    clip_projected_polygon_to_screen,
)


@dataclass(frozen=True)
class ProjectedRunway:
    low_left: ProjectedPoint
    low_right: ProjectedPoint
    high_left: ProjectedPoint
    high_right: ProjectedPoint

    clipped_points: tuple[
        ProjectedPoint,
        ...,
    ] = ()

    @property
    def polygon_points(
        self,
    ) -> tuple[
        ProjectedPoint,
        ...,
    ]:
        if len(self.clipped_points) >= 3:
            return self.clipped_points

        corners = (
            self.low_left,
            self.low_right,
            self.high_right,
            self.high_left,
        )

        if all(
            point.visible
            for point in corners
        ):
            return corners

        return ()

    @property
    def visible(self) -> bool:
        return (
            len(self.polygon_points)
            >= 3
        )


class RunwayProjectionComputer:
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
        geometry: RunwayGeometry,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
        width_px: int,
        height_px: int,
    ) -> ProjectedRunway | None:
        if (
            width_px <= 0
            or height_px <= 0
            or not isfinite(
                geometry.width_ft
            )
            or geometry.width_ft <= 0.0
            or not isfinite(
                self.near_plane_ft
            )
            or self.near_plane_ft <= 0.0
        ):
            return None

        delta_north = (
            geometry.high_end.north_ft
            - geometry.low_end.north_ft
        )

        delta_east = (
            geometry.high_end.east_ft
            - geometry.low_end.east_ft
        )

        centerline_length = hypot(
            delta_north,
            delta_east,
        )

        if (
            not isfinite(
                centerline_length
            )
            or centerline_length <= 0.0
        ):
            return None

        unit_north = (
            delta_north
            / centerline_length
        )

        unit_east = (
            delta_east
            / centerline_length
        )

        half_width = (
            geometry.width_ft
            / 2.0
        )

        left_north = (
            -unit_east
            * half_width
        )

        left_east = (
            unit_north
            * half_width
        )

        world_corners = (
            (
                geometry.low_end.north_ft
                + left_north,
                geometry.low_end.east_ft
                + left_east,
                geometry.low_end.up_ft,
            ),
            (
                geometry.low_end.north_ft
                - left_north,
                geometry.low_end.east_ft
                - left_east,
                geometry.low_end.up_ft,
            ),
            (
                geometry.high_end.north_ft
                - left_north,
                geometry.high_end.east_ft
                - left_east,
                geometry.high_end.up_ft,
            ),
            (
                geometry.high_end.north_ft
                + left_north,
                geometry.high_end.east_ft
                + left_east,
                geometry.high_end.up_ft,
            ),
        )

        orientation = (
            self.camera.prepare_orientation(
                heading_deg=heading_deg,
                pitch_deg=pitch_deg,
                roll_deg=roll_deg,
            )
        )

        if orientation is None:
            return None

        projection = (
            self.camera.prepare_projection(
                width_px=width_px,
                height_px=height_px,
                near_plane_ft=(
                    self.near_plane_ft
                ),
            )
        )

        if projection is None:
            return None

        camera_points: list[
            CameraPoint
        ] = []

        for (
            north_ft,
            east_ft,
            up_ft,
        ) in world_corners:
            camera_point = (
                self.camera
                .world_to_camera_prepared(
                    north_ft=north_ft,
                    east_ft=east_ft,
                    up_ft=up_ft,
                    orientation=orientation,
                )
            )

            if camera_point is None:
                return None

            camera_points.append(
                camera_point
            )

        raw_projected_points: list[
            ProjectedPoint
        ] = []

        for camera_point in camera_points:
            projected_point = (
                self.camera.project_prepared(
                    camera_point,
                    projection=projection,
                )
            )

            if projected_point is None:
                return None

            raw_projected_points.append(
                projected_point
            )

        low_left = (
            raw_projected_points[0]
        )

        low_right = (
            raw_projected_points[1]
        )

        high_right = (
            raw_projected_points[2]
        )

        high_left = (
            raw_projected_points[3]
        )

        clipped_camera_points = (
            clip_camera_polygon_to_near_plane(
                tuple(camera_points),
                near_plane_ft=(
                    self.near_plane_ft
                ),
            )
        )

        if not clipped_camera_points:
            return ProjectedRunway(
                low_left=low_left,
                low_right=low_right,
                high_left=high_left,
                high_right=high_right,
            )

        projected_polygon: list[
            ProjectedPoint
        ] = []

        for camera_point in (
            clipped_camera_points
        ):
            projected_point = (
                self.camera.project_prepared(
                    camera_point,
                    projection=projection,
                )
            )

            if projected_point is None:
                return None

            projected_polygon.append(
                projected_point
            )

        source_projected_polygon = (
            tuple(projected_polygon)
        )

        if all(
            point.visible
            for point
            in source_projected_polygon
        ):
            clipped_screen_points = (
                source_projected_polygon
            )
        else:
            clipped_screen_points = (
                clip_projected_polygon_to_screen(
                    source_projected_polygon,
                    width_px=width_px,
                    height_px=height_px,
                )
            )

        return ProjectedRunway(
            low_left=low_left,
            low_right=low_right,
            high_left=high_left,
            high_right=high_right,
            clipped_points=(
                clipped_screen_points
            ),
        )
