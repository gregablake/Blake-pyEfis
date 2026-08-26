from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, radians, sin


@dataclass(frozen=True)
class CameraPoint:
    right_ft: float
    up_ft: float
    forward_ft: float


@dataclass(frozen=True)
class ProjectedPoint:
    x_px: float
    y_px: float
    visible: bool


class SyntheticCamera:
    def world_to_camera(
        self,
        north_ft: float,
        east_ft: float,
        up_ft: float,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
    ) -> CameraPoint | None:
        values = (
            north_ft,
            east_ft,
            up_ft,
            heading_deg,
            pitch_deg,
            roll_deg,
        )

        if not all(isfinite(value) for value in values):
            return None

        heading = radians(heading_deg)
        pitch = radians(pitch_deg)
        roll = radians(roll_deg)

        forward_level = (
            north_ft * cos(heading)
            + east_ft * sin(heading)
        )

        right_level = (
            -north_ft * sin(heading)
            + east_ft * cos(heading)
        )

        up_pitched = (
            up_ft * cos(pitch)
            - forward_level * sin(pitch)
        )

        forward_pitched = (
            up_ft * sin(pitch)
            + forward_level * cos(pitch)
        )

        right_rolled = (
            right_level * cos(roll)
            + up_pitched * sin(roll)
        )

        up_rolled = (
            -right_level * sin(roll)
            + up_pitched * cos(roll)
        )

        return CameraPoint(
            right_ft=right_rolled,
            up_ft=up_rolled,
            forward_ft=forward_pitched,
        )

    def project(
        self,
        point: CameraPoint,
        width_px: int,
        height_px: int,
        horizontal_fov_deg: float = 70.0,
        vertical_fov_deg: float = 45.0,
        near_plane_ft: float = 5.0,
    ) -> ProjectedPoint | None:
        if (
            width_px <= 0
            or height_px <= 0
            or horizontal_fov_deg <= 0.0
            or vertical_fov_deg <= 0.0
            or near_plane_ft <= 0.0
        ):
            return None

        if not all(
            isfinite(value)
            for value in (
                point.right_ft,
                point.up_ft,
                point.forward_ft,
            )
        ):
            return None

        if point.forward_ft <= near_plane_ft:
            return ProjectedPoint(
                x_px=0.0,
                y_px=0.0,
                visible=False,
            )

        half_width = width_px / 2.0
        half_height = height_px / 2.0

        horizontal_scale = (
            half_width
            / (
                sin(radians(horizontal_fov_deg / 2.0))
                / cos(radians(horizontal_fov_deg / 2.0))
            )
        )

        vertical_scale = (
            half_height
            / (
                sin(radians(vertical_fov_deg / 2.0))
                / cos(radians(vertical_fov_deg / 2.0))
            )
        )

        x_px = (
            half_width
            + (
                point.right_ft
                / point.forward_ft
            )
            * horizontal_scale
        )

        y_px = (
            half_height
            - (
                point.up_ft
                / point.forward_ft
            )
            * vertical_scale
        )

        visible = (
            0.0 <= x_px <= width_px
            and 0.0 <= y_px <= height_px
        )

        return ProjectedPoint(
            x_px=x_px,
            y_px=y_px,
            visible=visible,
        )
