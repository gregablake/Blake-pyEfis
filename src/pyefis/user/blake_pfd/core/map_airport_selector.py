from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class MapAirportMarker:
    identifier: str
    screen_x: float
    screen_y: float
    distance_nm: float
    bearing_deg: float
    name: str = ""


@dataclass(frozen=True)
class MapAirportSelection:
    selected: bool = False
    identifier: str | None = None
    name: str = ""
    distance_nm: float | None = None
    bearing_deg: float | None = None
    screen_x: float | None = None
    screen_y: float | None = None


class MapAirportSelector:
    def __init__(
        self,
        *,
        touch_radius_px: float = 35.0,
    ) -> None:
        self.touch_radius_px = (
            self._require_positive(
                touch_radius_px,
                "touch_radius_px",
            )
        )

        self.selection = MapAirportSelection()

    def select_at(
        self,
        *,
        point_x,
        point_y,
        markers,
    ) -> MapAirportSelection:
        x = self._safe_number(
            point_x
        )

        y = self._safe_number(
            point_y
        )

        if x is None or y is None:
            return self.clear()

        best_marker = None
        best_distance_px = None

        for marker in markers:
            marker_x = self._safe_number(
                marker.screen_x
            )

            marker_y = self._safe_number(
                marker.screen_y
            )

            if (
                marker_x is None
                or marker_y is None
            ):
                continue

            distance_px = hypot(
                x - marker_x,
                y - marker_y,
            )

            if distance_px > self.touch_radius_px:
                continue

            if (
                best_distance_px is None
                or distance_px < best_distance_px
            ):
                best_marker = marker
                best_distance_px = distance_px

        if best_marker is None:
            return self.clear()

        self.selection = MapAirportSelection(
            selected=True,
            identifier=(
                str(
                    best_marker.identifier
                ).upper()
            ),
            name=str(
                best_marker.name
            ),
            distance_nm=float(
                best_marker.distance_nm
            ),
            bearing_deg=float(
                best_marker.bearing_deg
            ),
            screen_x=float(
                best_marker.screen_x
            ),
            screen_y=float(
                best_marker.screen_y
            ),
        )

        return self.selection

    def clear(
        self,
    ) -> MapAirportSelection:
        self.selection = MapAirportSelection()

        return self.selection

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

    @classmethod
    def _require_positive(
        cls,
        value,
        name: str,
    ) -> float:
        number = cls._safe_number(
            value
        )

        if (
            number is None
            or number <= 0.0
        ):
            raise ValueError(
                f"{name} must be finite and positive"
            )

        return number