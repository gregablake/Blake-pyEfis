from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, radians, sin


@dataclass(frozen=True)
class WindCalculation:
    wind_speed_kt: float = 0.0
    wind_from_deg: float = 0.0
    headwind_kt: float = 0.0
    tailwind_kt: float = 0.0
    crosswind_kt: float = 0.0
    crosswind_direction: str = "NONE"
    valid: bool = False


class WindCalculator:
    def calculate_components(
        self,
        wind_speed_kt,
        wind_from_deg,
        course_deg,
    ) -> WindCalculation:
        wind_speed = self._safe_nonnegative(
            wind_speed_kt
        )

        wind_from = self._safe_angle(
            wind_from_deg
        )

        course = self._safe_angle(
            course_deg
        )

        if (
            wind_speed is None
            or wind_from is None
            or course is None
        ):
            return WindCalculation()

        angle_deg = self._signed_angle_difference(
            wind_from,
            course,
        )

        angle_rad = radians(angle_deg)

        headwind_component = (
            wind_speed * cos(angle_rad)
        )

        crosswind_component = (
            wind_speed * sin(angle_rad)
        )

        headwind_kt = max(
            0.0,
            headwind_component,
        )

        tailwind_kt = max(
            0.0,
            -headwind_component,
        )

        crosswind_kt = abs(
            crosswind_component
        )

        if crosswind_kt < 0.05:
            crosswind_direction = "NONE"
        elif crosswind_component > 0.0:
            crosswind_direction = "RIGHT"
        else:
            crosswind_direction = "LEFT"

        return WindCalculation(
            wind_speed_kt=wind_speed,
            wind_from_deg=wind_from,
            headwind_kt=headwind_kt,
            tailwind_kt=tailwind_kt,
            crosswind_kt=crosswind_kt,
            crosswind_direction=crosswind_direction,
            valid=True,
        )

    @staticmethod
    def _signed_angle_difference(
        first_deg: float,
        second_deg: float,
    ) -> float:
        return (
            (first_deg - second_deg + 180.0)
            % 360.0
        ) - 180.0

    @staticmethod
    def _safe_nonnegative(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return max(
            0.0,
            number,
        )

    @staticmethod
    def _safe_angle(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return number % 360.0