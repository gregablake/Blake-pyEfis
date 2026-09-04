from __future__ import annotations

from dataclasses import dataclass
from math import cos, hypot, isfinite, radians, sin


@dataclass(frozen=True)
class SafeTaxiPoint:
    x: float
    y: float


@dataclass(frozen=True)
class SafeTaxiProjectedRunway:
    airport_ident: str
    low_ident: str
    high_ident: str

    low_center_x: float
    low_center_y: float
    high_center_x: float
    high_center_y: float

    corners: tuple[
        SafeTaxiPoint,
        SafeTaxiPoint,
        SafeTaxiPoint,
        SafeTaxiPoint,
    ]


@dataclass(frozen=True)
class SafeTaxiProjectionState:
    valid: bool = False
    ownship_x: float = 0.0
    ownship_y: float = 0.0
    runways: tuple[
        SafeTaxiProjectedRunway,
        ...,
    ] = ()


class SafeTaxiMapProjector:
    """
    Project aircraft-relative runway geometry onto a
    heading-up top-down airport surface display.

    The aircraft remains fixed at the center of the display.

    range_ft represents the distance from the aircraft to
    either the top or bottom edge of the screen.
    """

    def __init__(
        self,
        range_ft: float = 3000.0,
    ) -> None:
        try:
            safe_range = float(range_ft)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Safe Taxi range must be finite and positive"
            ) from exc

        if (
            not isfinite(safe_range)
            or safe_range <= 0.0
        ):
            raise ValueError(
                "Safe Taxi range must be finite and positive"
            )

        self.range_ft = safe_range

    @staticmethod
    def _finite(value) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(result):
            return None

        return result

    @staticmethod
    def _invalid() -> SafeTaxiProjectionState:
        return SafeTaxiProjectionState()

    def project(
        self,
        *,
        runways,
        heading_deg: float,
        width_px: int,
        height_px: int,
    ) -> SafeTaxiProjectionState:
        heading = self._finite(
            heading_deg
        )

        width = self._finite(
            width_px
        )

        height = self._finite(
            height_px
        )

        if (
            heading is None
            or width is None
            or height is None
            or width <= 0.0
            or height <= 0.0
        ):
            return self._invalid()

        ownship_x = width / 2.0
        ownship_y = height / 2.0

        # Preserve one physical scale in both axes.
        #
        # Example:
        # 600 px display height with range_ft=1000
        # means 2000 ft from bottom to top:
        #
        #     600 / 2000 = 0.3 px/ft
        #
        pixels_per_ft = (
            height
            / (2.0 * self.range_ft)
        )

        heading_rad = radians(
            heading % 360.0
        )

        heading_cos = cos(
            heading_rad
        )

        heading_sin = sin(
            heading_rad
        )

        projected_runways = []

        for runway in runways:
            projected = self._project_runway(
                runway=runway,
                ownship_x=ownship_x,
                ownship_y=ownship_y,
                pixels_per_ft=pixels_per_ft,
                heading_cos=heading_cos,
                heading_sin=heading_sin,
            )

            if projected is not None:
                projected_runways.append(
                    projected
                )

        return SafeTaxiProjectionState(
            valid=True,
            ownship_x=ownship_x,
            ownship_y=ownship_y,
            runways=tuple(
                projected_runways
            ),
        )

    def _project_runway(
        self,
        *,
        runway,
        ownship_x: float,
        ownship_y: float,
        pixels_per_ft: float,
        heading_cos: float,
        heading_sin: float,
    ) -> SafeTaxiProjectedRunway | None:
        try:
            low = runway.low_end
            high = runway.high_end
        except AttributeError:
            return None

        low_xy = self._project_local_point(
            north_ft=getattr(
                low,
                "north_ft",
                None,
            ),
            east_ft=getattr(
                low,
                "east_ft",
                None,
            ),
            ownship_x=ownship_x,
            ownship_y=ownship_y,
            pixels_per_ft=pixels_per_ft,
            heading_cos=heading_cos,
            heading_sin=heading_sin,
        )

        high_xy = self._project_local_point(
            north_ft=getattr(
                high,
                "north_ft",
                None,
            ),
            east_ft=getattr(
                high,
                "east_ft",
                None,
            ),
            ownship_x=ownship_x,
            ownship_y=ownship_y,
            pixels_per_ft=pixels_per_ft,
            heading_cos=heading_cos,
            heading_sin=heading_sin,
        )

        runway_width_ft = self._finite(
            getattr(
                runway,
                "width_ft",
                None,
            )
        )

        if (
            low_xy is None
            or high_xy is None
            or runway_width_ft is None
            or runway_width_ft <= 0.0
        ):
            return None

        dx = high_xy.x - low_xy.x
        dy = high_xy.y - low_xy.y

        centerline_length_px = hypot(
            dx,
            dy,
        )

        if (
            not isfinite(centerline_length_px)
            or centerline_length_px <= 0.0
        ):
            return None

        half_width_px = (
            runway_width_ft
            * pixels_per_ft
            / 2.0
        )

        # Unit vector perpendicular to runway centerline.
        perpendicular_x = (
            -dy
            / centerline_length_px
        )

        perpendicular_y = (
            dx
            / centerline_length_px
        )

        offset_x = (
            perpendicular_x
            * half_width_px
        )

        offset_y = (
            perpendicular_y
            * half_width_px
        )

        corners = (
            SafeTaxiPoint(
                x=low_xy.x + offset_x,
                y=low_xy.y + offset_y,
            ),
            SafeTaxiPoint(
                x=high_xy.x + offset_x,
                y=high_xy.y + offset_y,
            ),
            SafeTaxiPoint(
                x=high_xy.x - offset_x,
                y=high_xy.y - offset_y,
            ),
            SafeTaxiPoint(
                x=low_xy.x - offset_x,
                y=low_xy.y - offset_y,
            ),
        )

        return SafeTaxiProjectedRunway(
            airport_ident=str(
                getattr(
                    runway,
                    "airport_ident",
                    "",
                )
            ),
            low_ident=str(
                getattr(
                    low,
                    "ident",
                    "",
                )
            ),
            high_ident=str(
                getattr(
                    high,
                    "ident",
                    "",
                )
            ),
            low_center_x=low_xy.x,
            low_center_y=low_xy.y,
            high_center_x=high_xy.x,
            high_center_y=high_xy.y,
            corners=corners,
        )

    def _project_local_point(
        self,
        *,
        north_ft,
        east_ft,
        ownship_x: float,
        ownship_y: float,
        pixels_per_ft: float,
        heading_cos: float,
        heading_sin: float,
    ) -> SafeTaxiPoint | None:
        north = self._finite(
            north_ft
        )

        east = self._finite(
            east_ft
        )

        if (
            north is None
            or east is None
        ):
            return None

        # Rotate north/east coordinates into aircraft-relative
        # heading-up coordinates.
        #
        # forward_ft is positive toward the top of the display.
        # right_ft is positive toward the right side.
        forward_ft = (
            north * heading_cos
            + east * heading_sin
        )

        right_ft = (
            -north * heading_sin
            + east * heading_cos
        )

        x = (
            ownship_x
            + right_ft * pixels_per_ft
        )

        y = (
            ownship_y
            - forward_ft * pixels_per_ft
        )

        if (
            not isfinite(x)
            or not isfinite(y)
        ):
            return None

        return SafeTaxiPoint(
            x=x,
            y=y,
        )
