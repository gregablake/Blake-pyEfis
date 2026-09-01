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


@dataclass(frozen=True)
class CameraOrientation:
    heading_cos: float
    heading_sin: float
    pitch_cos: float
    pitch_sin: float
    roll_cos: float
    roll_sin: float


@dataclass(frozen=True)
class CameraProjection:
    width_px: int
    height_px: int
    half_width: float
    half_height: float
    horizontal_scale: float
    vertical_scale: float
    near_plane_ft: float


class SyntheticCamera:
    def prepare_orientation(
        self,
        *,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
    ) -> CameraOrientation | None:
        values = (
            heading_deg,
            pitch_deg,
            roll_deg,
        )

        if not all(
            isfinite(value)
            for value in values
        ):
            return None

        heading = radians(heading_deg)
        pitch = radians(pitch_deg)
        roll = radians(roll_deg)

        return CameraOrientation(
            heading_cos=cos(heading),
            heading_sin=sin(heading),
            pitch_cos=cos(pitch),
            pitch_sin=sin(pitch),
            roll_cos=cos(roll),
            roll_sin=sin(roll),
        )

    def world_to_camera(
        self,
        north_ft: float,
        east_ft: float,
        up_ft: float,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
    ) -> CameraPoint | None:
        orientation = self.prepare_orientation(
            heading_deg=heading_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
        )

        if orientation is None:
            return None

        return self.world_to_camera_prepared(
            north_ft=north_ft,
            east_ft=east_ft,
            up_ft=up_ft,
            orientation=orientation,
        )

    def world_to_camera_prepared(
        self,
        *,
        north_ft: float,
        east_ft: float,
        up_ft: float,
        orientation: CameraOrientation,
    ) -> CameraPoint | None:
        if not isinstance(
            orientation,
            CameraOrientation,
        ):
            return None

        if not all(
            isfinite(value)
            for value in (
                north_ft,
                east_ft,
                up_ft,
            )
        ):
            return None

        forward_level = (
            north_ft * orientation.heading_cos
            + east_ft * orientation.heading_sin
        )

        right_level = (
            -north_ft * orientation.heading_sin
            + east_ft * orientation.heading_cos
        )

        up_pitched = (
            up_ft * orientation.pitch_cos
            - forward_level
            * orientation.pitch_sin
        )

        forward_pitched = (
            up_ft * orientation.pitch_sin
            + forward_level
            * orientation.pitch_cos
        )

        right_rolled = (
            right_level * orientation.roll_cos
            + up_pitched * orientation.roll_sin
        )

        up_rolled = (
            -right_level * orientation.roll_sin
            + up_pitched * orientation.roll_cos
        )

        return CameraPoint(
            right_ft=right_rolled,
            up_ft=up_rolled,
            forward_ft=forward_pitched,
        )

    def prepare_projection(
        self,
        *,
        width_px: int,
        height_px: int,
        horizontal_fov_deg: float = 70.0,
        vertical_fov_deg: float = 45.0,
        near_plane_ft: float = 5.0,
    ) -> CameraProjection | None:
        if not all(
            isfinite(value)
            for value in (
                width_px,
                height_px,
                horizontal_fov_deg,
                vertical_fov_deg,
                near_plane_ft,
            )
        ):
            return None

        if (
            width_px <= 0
            or height_px <= 0
            or horizontal_fov_deg <= 0.0
            or vertical_fov_deg <= 0.0
            or near_plane_ft <= 0.0
        ):
            return None

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

        return CameraProjection(
            width_px=width_px,
            height_px=height_px,
            half_width=half_width,
            half_height=half_height,
            horizontal_scale=horizontal_scale,
            vertical_scale=vertical_scale,
            near_plane_ft=near_plane_ft,
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
        projection = self.prepare_projection(
            width_px=width_px,
            height_px=height_px,
            horizontal_fov_deg=horizontal_fov_deg,
            vertical_fov_deg=vertical_fov_deg,
            near_plane_ft=near_plane_ft,
        )

        if projection is None:
            return None

        return self.project_prepared(
            point,
            projection=projection,
        )

    def project_prepared(
        self,
        point: CameraPoint,
        *,
        projection: CameraProjection,
    ) -> ProjectedPoint | None:
        if not isinstance(
            projection,
            CameraProjection,
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

        if (
            point.forward_ft
            < projection.near_plane_ft
        ):
            return ProjectedPoint(
                x_px=0.0,
                y_px=0.0,
                visible=False,
            )

        x_px = (
            projection.half_width
            + (
                point.right_ft
                / point.forward_ft
            )
            * projection.horizontal_scale
        )

        y_px = (
            projection.half_height
            - (
                point.up_ft
                / point.forward_ft
            )
            * projection.vertical_scale
        )

        visible = (
            0.0
            <= x_px
            <= projection.width_px
            and 0.0
            <= y_px
            <= projection.height_px
        )

        return ProjectedPoint(
            x_px=x_px,
            y_px=y_px,
            visible=visible,
        )
