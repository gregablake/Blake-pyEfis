from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class MapViewportState:
    offset_x_px: float = 0.0
    offset_y_px: float = 0.0
    centered: bool = True


class MapViewport:
    def __init__(
        self,
        *,
        maximum_offset_px: float = 500.0,
    ) -> None:
        self.maximum_offset_px = (
            self._require_positive(
                maximum_offset_px,
                "maximum_offset_px",
            )
        )

        self.state = MapViewportState()

    def pan_by(
        self,
        *,
        delta_x_px,
        delta_y_px,
    ) -> MapViewportState:
        delta_x = self._safe_number(
            delta_x_px
        )

        delta_y = self._safe_number(
            delta_y_px
        )

        if (
            delta_x is None
            or delta_y is None
        ):
            return self.state

        offset_x = self._clamp(
            self.state.offset_x_px
            + delta_x,
            -self.maximum_offset_px,
            self.maximum_offset_px,
        )

        offset_y = self._clamp(
            self.state.offset_y_px
            + delta_y,
            -self.maximum_offset_px,
            self.maximum_offset_px,
        )

        self.state = MapViewportState(
            offset_x_px=offset_x,
            offset_y_px=offset_y,
            centered=(
                offset_x == 0.0
                and offset_y == 0.0
            ),
        )

        return self.state

    def center(self) -> MapViewportState:
        self.state = MapViewportState()

        return self.state

    @staticmethod
    def _clamp(
        value: float,
        low: float,
        high: float,
    ) -> float:
        return max(
            low,
            min(
                high,
                value,
            ),
        )

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