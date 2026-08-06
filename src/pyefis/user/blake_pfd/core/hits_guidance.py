from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class HitsGuidanceBox:
    depth_fraction: float
    center_x_fraction: float
    center_y_fraction: float
    width_fraction: float
    height_fraction: float


@dataclass(frozen=True)
class HitsGuidanceState:
    boxes: tuple[HitsGuidanceBox, ...] = ()
    lateral_error: float = 0.0
    vertical_error: float = 0.0
    valid: bool = False


class HitsGuidance:
    def __init__(
        self,
        *,
        box_count: int = 6,
        lateral_scale: float = 0.28,
        vertical_scale: float = 0.22,
        near_width_fraction: float = 0.34,
        near_height_fraction: float = 0.24,
        far_width_fraction: float = 0.08,
        far_height_fraction: float = 0.06,
    ) -> None:
        if box_count < 2:
            raise ValueError(
                "box_count must be at least 2"
            )

        self.box_count = int(box_count)

        self.lateral_scale = self._require_positive(
            lateral_scale,
            "lateral_scale",
        )
        self.vertical_scale = self._require_positive(
            vertical_scale,
            "vertical_scale",
        )
        self.near_width_fraction = (
            self._require_fraction(
                near_width_fraction,
                "near_width_fraction",
            )
        )
        self.near_height_fraction = (
            self._require_fraction(
                near_height_fraction,
                "near_height_fraction",
            )
        )
        self.far_width_fraction = (
            self._require_fraction(
                far_width_fraction,
                "far_width_fraction",
            )
        )
        self.far_height_fraction = (
            self._require_fraction(
                far_height_fraction,
                "far_height_fraction",
            )
        )

        if (
            self.far_width_fraction
            >= self.near_width_fraction
        ):
            raise ValueError(
                "far_width_fraction must be smaller "
                "than near_width_fraction"
            )

        if (
            self.far_height_fraction
            >= self.near_height_fraction
        ):
            raise ValueError(
                "far_height_fraction must be smaller "
                "than near_height_fraction"
            )

    def calculate(
        self,
        *,
        cdi,
        vdi,
        navigation_valid: bool = True,
    ) -> HitsGuidanceState:
        if not navigation_valid:
            return HitsGuidanceState()

        lateral_error = self._safe_clamped(
            cdi,
            -1.0,
            1.0,
        )
        vertical_error = self._safe_clamped(
            vdi,
            -1.0,
            1.0,
        )

        if (
            lateral_error is None
            or vertical_error is None
        ):
            return HitsGuidanceState()

        boxes: list[HitsGuidanceBox] = []

        for index in range(
            self.box_count
        ):
            depth_fraction = (
                index
                / (
                    self.box_count
                    - 1
                )
            )

            perspective = (
                1.0
                - depth_fraction
            )

            center_x_fraction = (
                0.5
                - lateral_error
                * self.lateral_scale
                * perspective
            )

            center_y_fraction = (
                0.5
                + vertical_error
                * self.vertical_scale
                * perspective
            )

            width_fraction = self._interpolate(
                self.near_width_fraction,
                self.far_width_fraction,
                depth_fraction,
            )

            height_fraction = self._interpolate(
                self.near_height_fraction,
                self.far_height_fraction,
                depth_fraction,
            )

            boxes.append(
                HitsGuidanceBox(
                    depth_fraction=depth_fraction,
                    center_x_fraction=(
                        center_x_fraction
                    ),
                    center_y_fraction=(
                        center_y_fraction
                    ),
                    width_fraction=width_fraction,
                    height_fraction=height_fraction,
                )
            )

        return HitsGuidanceState(
            boxes=tuple(boxes),
            lateral_error=lateral_error,
            vertical_error=vertical_error,
            valid=True,
        )

    @staticmethod
    def _interpolate(
        near_value: float,
        far_value: float,
        fraction: float,
    ) -> float:
        return (
            near_value
            + (
                far_value
                - near_value
            )
            * fraction
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
    def _safe_clamped(
        cls,
        value,
        low: float,
        high: float,
    ) -> float | None:
        number = cls._safe_number(
            value
        )

        if number is None:
            return None

        return max(
            low,
            min(
                high,
                number,
            ),
        )

    @classmethod
    def _require_positive(
        cls,
        value,
        name: str,
    ) -> float:
        number = cls._safe_number(
            value
        )

        if number is None or number <= 0.0:
            raise ValueError(
                f"{name} must be finite and positive"
            )

        return number

    @classmethod
    def _require_fraction(
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
            or number > 1.0
        ):
            raise ValueError(
                f"{name} must be greater than 0 "
                "and no greater than 1"
            )

        return number