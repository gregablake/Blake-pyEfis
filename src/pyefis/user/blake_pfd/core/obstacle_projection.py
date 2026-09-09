from __future__ import annotations

from dataclasses import dataclass
from math import (
    cos,
    isfinite,
    radians,
    sin,
)

from pyefis.user.blake_pfd.core.synthetic_camera import (
    SyntheticCamera,
)
from pyefis.user.blake_pfd.obstacles import (
    Obstacle,
    obstacle_is_threat,
)


FEET_PER_NM = 6076.12


@dataclass(frozen=True)
class ProjectedObstacle:
    ident: str
    x_px: float
    y_px: float
    distance_nm: float
    bearing_deg: float
    elevation_ft: float
    height_agl_ft: float
    threat: bool


class ObstacleProjectionComputer:
    """
    Project FAA obstacle tops into synthetic vision.

    Projection uses obstacle-top AMSL elevation relative
    to aircraft indicated altitude.

    The per-obstacle threat flag mirrors the existing
    obstacle-warning predicate for depiction only.
    This class does not create or latch warning state.
    """

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
        obstacles,
        aircraft_alt_ft: float,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
        width_px: int,
        height_px: int,
        warning_distance_nm: float = 3.0,
        warning_clearance_ft: float = 1000.0,
    ) -> list[ProjectedObstacle]:
        if not self._frame_valid(
            aircraft_alt_ft=aircraft_alt_ft,
            heading_deg=heading_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            width_px=width_px,
            height_px=height_px,
            warning_distance_nm=(
                warning_distance_nm
            ),
            warning_clearance_ft=(
                warning_clearance_ft
            ),
        ):
            return []

        orientation = (
            self.camera.prepare_orientation(
                heading_deg=heading_deg,
                pitch_deg=pitch_deg,
                roll_deg=roll_deg,
            )
        )

        if orientation is None:
            return []

        projection = (
            self.camera.prepare_projection(
                width_px=width_px,
                height_px=height_px,
            )
        )

        if projection is None:
            return []

        try:
            obstacle_items = tuple(
                obstacles
            )
        except TypeError:
            return []

        projected: list[
            ProjectedObstacle
        ] = []

        for obstacle in obstacle_items:
            if not self._obstacle_valid(
                obstacle
            ):
                continue

            bearing_rad = radians(
                obstacle.bearing_deg
            )

            distance_ft = (
                obstacle.distance_nm
                * FEET_PER_NM
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
                obstacle.elevation_ft
                - aircraft_alt_ft
            )

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
                continue

            screen_point = (
                self.camera.project_prepared(
                    camera_point,
                    projection=projection,
                )
            )

            if (
                screen_point is None
                or not screen_point.visible
            ):
                continue

            projected.append(
                ProjectedObstacle(
                    ident=obstacle.ident,
                    x_px=screen_point.x_px,
                    y_px=screen_point.y_px,
                    distance_nm=(
                        obstacle.distance_nm
                    ),
                    bearing_deg=(
                        obstacle.bearing_deg
                    ),
                    elevation_ft=(
                        obstacle.elevation_ft
                    ),
                    height_agl_ft=(
                        obstacle.height_agl_ft
                    ),
                    threat=obstacle_is_threat(
                        obstacle=obstacle,
                        aircraft_alt_ft=(
                            aircraft_alt_ft
                        ),
                        warning_distance_nm=(
                            warning_distance_nm
                        ),
                        warning_clearance_ft=(
                            warning_clearance_ft
                        ),
                    ),
                )
            )

        return projected

    @staticmethod
    def _frame_valid(
        *,
        aircraft_alt_ft: float,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
        width_px: int,
        height_px: int,
        warning_distance_nm: float,
        warning_clearance_ft: float,
    ) -> bool:
        values = (
            aircraft_alt_ft,
            heading_deg,
            pitch_deg,
            roll_deg,
            width_px,
            height_px,
            warning_distance_nm,
            warning_clearance_ft,
        )

        return (
            all(
                isfinite(value)
                for value in values
            )
            and width_px > 0
            and height_px > 0
            and warning_distance_nm > 0.0
            and warning_clearance_ft >= 0.0
        )

    @staticmethod
    def _obstacle_valid(
        obstacle,
    ) -> bool:
        if not isinstance(
            obstacle,
            Obstacle,
        ):
            return False

        if (
            not isinstance(
                obstacle.ident,
                str,
            )
            or not obstacle.ident.strip()
        ):
            return False

        values = (
            obstacle.distance_nm,
            obstacle.bearing_deg,
            obstacle.elevation_ft,
            obstacle.height_agl_ft,
        )

        return (
            all(
                isfinite(value)
                for value in values
            )
            and obstacle.distance_nm >= 0.0
            and obstacle.height_agl_ft >= 0.0
        )
