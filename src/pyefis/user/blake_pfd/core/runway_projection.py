from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite

from pyefis.user.blake_pfd.core.runway_geometry import (
    RunwayGeometry,
)
from pyefis.user.blake_pfd.core.synthetic_camera import (
    ProjectedPoint,
    SyntheticCamera,
)


@dataclass(frozen=True)
class ProjectedRunway:
    low_left: ProjectedPoint
    low_right: ProjectedPoint
    high_left: ProjectedPoint
    high_right: ProjectedPoint

    @property
    def visible(self) -> bool:
        return all(
            point.visible
            for point in (
                self.low_left,
                self.low_right,
                self.high_left,
                self.high_right,
            )
        )


class RunwayProjectionComputer:
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
            or not isfinite(geometry.width_ft)
            or geometry.width_ft <= 0.0
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
            not isfinite(centerline_length)
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

        half_width = geometry.width_ft / 2.0

        left_north = (
            -unit_east
            * half_width
        )

        left_east = (
            unit_north
            * half_width
        )

        low_left = self._project_corner(
            north_ft=(
                geometry.low_end.north_ft
                + left_north
            ),
            east_ft=(
                geometry.low_end.east_ft
                + left_east
            ),
            up_ft=geometry.low_end.up_ft,
            heading_deg=heading_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            width_px=width_px,
            height_px=height_px,
        )

        low_right = self._project_corner(
            north_ft=(
                geometry.low_end.north_ft
                - left_north
            ),
            east_ft=(
                geometry.low_end.east_ft
                - left_east
            ),
            up_ft=geometry.low_end.up_ft,
            heading_deg=heading_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            width_px=width_px,
            height_px=height_px,
        )

        high_left = self._project_corner(
            north_ft=(
                geometry.high_end.north_ft
                + left_north
            ),
            east_ft=(
                geometry.high_end.east_ft
                + left_east
            ),
            up_ft=geometry.high_end.up_ft,
            heading_deg=heading_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            width_px=width_px,
            height_px=height_px,
        )

        high_right = self._project_corner(
            north_ft=(
                geometry.high_end.north_ft
                - left_north
            ),
            east_ft=(
                geometry.high_end.east_ft
                - left_east
            ),
            up_ft=geometry.high_end.up_ft,
            heading_deg=heading_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            width_px=width_px,
            height_px=height_px,
        )

        if (
            low_left is None
            or low_right is None
            or high_left is None
            or high_right is None
        ):
            return None

        return ProjectedRunway(
            low_left=low_left,
            low_right=low_right,
            high_left=high_left,
            high_right=high_right,
        )

    def _project_corner(
        self,
        north_ft: float,
        east_ft: float,
        up_ft: float,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
        width_px: int,
        height_px: int,
    ) -> ProjectedPoint | None:
        camera_point = self.camera.world_to_camera(
            north_ft=north_ft,
            east_ft=east_ft,
            up_ft=up_ft,
            heading_deg=heading_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
        )

        if camera_point is None:
            return None

        return self.camera.project(
            camera_point,
            width_px=width_px,
            height_px=height_px,
        )
