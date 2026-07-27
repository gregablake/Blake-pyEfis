from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class CalculatedFuelState:
    remaining_gal: float = 0.0
    used_gal: float = 0.0
    flow_gph: float = 0.0
    endurance_hr: float = 0.0
    range_nm: float = 0.0
    calculation_valid: bool = False


class FuelStateCalculator:
    def __init__(
        self,
        minimum_flow_gph: float = 0.1,
        minimum_ground_speed_kt: float = 20.0,
    ) -> None:
        if (
            not isfinite(minimum_flow_gph)
            or minimum_flow_gph <= 0.0
        ):
            raise ValueError(
                "minimum_flow_gph must be finite and positive"
            )

        if (
            not isfinite(minimum_ground_speed_kt)
            or minimum_ground_speed_kt <= 0.0
        ):
            raise ValueError(
                "minimum_ground_speed_kt must be finite and positive"
            )

        self.minimum_flow_gph = float(
            minimum_flow_gph
        )

        self.minimum_ground_speed_kt = float(
            minimum_ground_speed_kt
        )

    def calculate(
        self,
        remaining_gal,
        used_gal,
        flow_gph,
        ground_speed_kt,
        fallback_endurance_hr=0.0,
        fallback_range_nm=0.0,
    ) -> CalculatedFuelState:
        safe_remaining_gal = self._safe_nonnegative(
            remaining_gal
        )

        safe_used_gal = self._safe_nonnegative(
            used_gal
        )

        safe_flow_gph = self._safe_nonnegative(
            flow_gph
        )

        safe_ground_speed_kt = self._safe_nonnegative(
            ground_speed_kt
        )

        if safe_flow_gph < self.minimum_flow_gph:
            return CalculatedFuelState(
                remaining_gal=safe_remaining_gal,
                used_gal=safe_used_gal,
                flow_gph=safe_flow_gph,
                endurance_hr=self._safe_nonnegative(
                    fallback_endurance_hr
                ),
                range_nm=self._safe_nonnegative(
                    fallback_range_nm
                ),
                calculation_valid=False,
            )

        endurance_hr = (
            safe_remaining_gal
            / safe_flow_gph
        )

        if (
            safe_ground_speed_kt
            >= self.minimum_ground_speed_kt
        ):
            range_nm = (
                endurance_hr
                * safe_ground_speed_kt
            )
        else:
            range_nm = self._safe_nonnegative(
                fallback_range_nm
            )

        return CalculatedFuelState(
            remaining_gal=safe_remaining_gal,
            used_gal=safe_used_gal,
            flow_gph=safe_flow_gph,
            endurance_hr=endurance_hr,
            range_nm=range_nm,
            calculation_valid=True,
        )

    @staticmethod
    def _safe_nonnegative(value) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0

        if not isfinite(number):
            return 0.0

        return max(
            0.0,
            number,
        )