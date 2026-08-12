from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class DirectToGuidanceState:
    active: bool = False
    identifier: str | None = None
    bearing_deg: float | None = None
    distance_nm: float | None = None
    course_error_deg: float | None = None


class DirectToGuidance:
    def __init__(self) -> None:
        self.state = DirectToGuidanceState()

    def update(
        self,
        *,
        direct_to_state,
        aircraft_track_deg,
    ) -> DirectToGuidanceState:
        if not getattr(
            direct_to_state,
            "active",
            False,
        ):
            return self.clear()

        bearing_deg = self._safe_number(
            getattr(
                direct_to_state,
                "bearing_deg",
                None,
            )
        )

        distance_nm = self._safe_number(
            getattr(
                direct_to_state,
                "distance_nm",
                None,
            )
        )

        track_deg = self._safe_number(
            aircraft_track_deg
        )

        if (
            bearing_deg is None
            or distance_nm is None
            or track_deg is None
        ):
            return self.clear()

        course_error_deg = (
            bearing_deg
            - track_deg
            + 180.0
        ) % 360.0 - 180.0

        self.state = DirectToGuidanceState(
            active=True,
            identifier=getattr(
                direct_to_state,
                "identifier",
                None,
            ),
            bearing_deg=(
                bearing_deg % 360.0
            ),
            distance_nm=max(
                0.0,
                distance_nm,
            ),
            course_error_deg=(
                course_error_deg
            ),
        )

        return self.state

    def clear(
        self,
    ) -> DirectToGuidanceState:
        self.state = (
            DirectToGuidanceState()
        )

        return self.state

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