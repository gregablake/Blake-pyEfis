from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class DirectToLateralGuidanceState:
    active: bool = False
    lateral_error: float = 0.0
    course_error_deg: float = 0.0


class DirectToLateralGuidance:
    def __init__(
        self,
        *,
        full_scale_error_deg: float = 20.0,
    ) -> None:
        self.full_scale_error_deg = (
            self._require_positive(
                full_scale_error_deg,
                "full_scale_error_deg",
            )
        )

        self.state = (
            DirectToLateralGuidanceState()
        )

    def update(
        self,
        *,
        guidance_state,
    ) -> DirectToLateralGuidanceState:
        if not getattr(
            guidance_state,
            "active",
            False,
        ):
            return self.clear()

        course_error_deg = (
            self._safe_number(
                getattr(
                    guidance_state,
                    "course_error_deg",
                    None,
                )
            )
        )

        if course_error_deg is None:
            return self.clear()

        normalized_error = (
            -course_error_deg
            / self.full_scale_error_deg
        )

        normalized_error = max(
            -1.0,
            min(
                1.0,
                normalized_error,
            ),
        )

        self.state = (
            DirectToLateralGuidanceState(
                active=True,
                lateral_error=normalized_error,
                course_error_deg=(
                    course_error_deg
                ),
            )
        )

        return self.state

    def clear(
        self,
    ) -> DirectToLateralGuidanceState:
        self.state = (
            DirectToLateralGuidanceState()
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

    @staticmethod
    def _require_positive(
        value,
        name: str,
    ) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{name} must be finite and positive"
            )

        if (
            not isfinite(number)
            or number <= 0.0
        ):
            raise ValueError(
                f"{name} must be finite and positive"
            )

        return number