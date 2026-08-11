from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class MapOrientationState:
    mode: str = "NORTH_UP"
    reference_deg: float = 0.0


class MapOrientation:
    VALID_MODES = (
        "NORTH_UP",
        "TRACK_UP",
    )

    def __init__(
        self,
        *,
        mode: str = "NORTH_UP",
    ) -> None:
        self.state = MapOrientationState(
            mode=self._normalize_mode(
                mode
            ),
            reference_deg=0.0,
        )

    def set_mode(
        self,
        mode: str,
    ) -> MapOrientationState:
        self.state = MapOrientationState(
            mode=self._normalize_mode(
                mode
            ),
            reference_deg=(
                self.state.reference_deg
            ),
        )

        return self.state

    def toggle(
        self,
    ) -> MapOrientationState:
        if self.state.mode == "NORTH_UP":
            return self.set_mode(
                "TRACK_UP"
            )

        return self.set_mode(
            "NORTH_UP"
        )

    def update_reference(
        self,
        *,
        track_deg,
    ) -> MapOrientationState:
        track = self._safe_number(
            track_deg
        )

        if track is None:
            track = 0.0

        if self.state.mode == "TRACK_UP":
            reference = (
                track % 360.0
            )
        else:
            reference = 0.0

        self.state = MapOrientationState(
            mode=self.state.mode,
            reference_deg=reference,
        )

        return self.state

    def relative_bearing_deg(
        self,
        *,
        bearing_deg,
    ) -> float | None:
        bearing = self._safe_number(
            bearing_deg
        )

        if bearing is None:
            return None

        relative = (
            bearing
            - self.state.reference_deg
        ) % 360.0

        return relative

    @classmethod
    def _normalize_mode(
        cls,
        mode,
    ) -> str:
        normalized = str(
            mode
        ).strip().upper()

        if normalized not in cls.VALID_MODES:
            raise ValueError(
                "mode must be NORTH_UP or TRACK_UP"
            )

        return normalized

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