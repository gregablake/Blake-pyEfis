from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class FuelAdvice:
    severity: str = "NORMAL"
    title: str = "Fuel Normal"
    reason: str = "Fuel reserve is adequate."
    action: str = "Continue monitoring fuel."
    endurance_hr: float | None = None
    time_to_destination_hr: float | None = None
    reserve_at_destination_hr: float | None = None
    fuel_at_destination_gal: float | None = None


class FuelAdvisor:
    def __init__(
        self,
        caution_reserve_min: float = 45.0,
        warning_reserve_min: float = 30.0,
        minimum_ground_speed_kt: float = 20.0,
        minimum_fuel_flow_gph: float = 0.1,
    ) -> None:
        if caution_reserve_min < warning_reserve_min:
            raise ValueError(
                "caution_reserve_min must be greater than "
                "or equal to warning_reserve_min"
            )

        if warning_reserve_min < 0.0:
            raise ValueError(
                "warning_reserve_min must not be negative"
            )

        if minimum_ground_speed_kt <= 0.0:
            raise ValueError(
                "minimum_ground_speed_kt must be positive"
            )

        if minimum_fuel_flow_gph <= 0.0:
            raise ValueError(
                "minimum_fuel_flow_gph must be positive"
            )

        self.caution_reserve_hr = (
            float(caution_reserve_min) / 60.0
        )

        self.warning_reserve_hr = (
            float(warning_reserve_min) / 60.0
        )

        self.minimum_ground_speed_kt = float(
            minimum_ground_speed_kt
        )

        self.minimum_fuel_flow_gph = float(
            minimum_fuel_flow_gph
        )

    def advise(
        self,
        fuel_state,
        navigation_state=None,
        ground_speed_kt: float = 0.0,
    ) -> FuelAdvice:
        if fuel_state is None:
            return FuelAdvice(
                severity="NORMAL",
                title="Fuel Data Unavailable",
                reason="Fuel state is unavailable.",
                action="Verify fuel quantity and fuel-flow inputs.",
            )

        remaining_gal = self._safe_nonnegative(
            getattr(
                fuel_state,
                "remaining_gal",
                0.0,
            )
        )

        flow_gph = self._safe_nonnegative(
            getattr(
                fuel_state,
                "flow_gph",
                0.0,
            )
        )

        if flow_gph < self.minimum_fuel_flow_gph:
            return FuelAdvice(
                severity="NORMAL",
                title="Fuel Flow Unavailable",
                reason=(
                    "Fuel flow is too low to calculate "
                    "reliable endurance."
                ),
                action=(
                    "Verify the fuel-flow sensor and monitor "
                    "fuel quantity manually."
                ),
            )

        endurance_hr = remaining_gal / flow_gph

        distance_nm = self._safe_nonnegative(
            getattr(
                navigation_state,
                "distance_nm",
                0.0,
            )
        )

        safe_ground_speed_kt = self._safe_nonnegative(
            ground_speed_kt
        )

        if (
            navigation_state is None
            or distance_nm <= 0.0
            or safe_ground_speed_kt
            < self.minimum_ground_speed_kt
        ):
            return self._endurance_only_advice(
                endurance_hr=endurance_hr,
            )

        time_to_destination_hr = (
            distance_nm / safe_ground_speed_kt
        )

        reserve_at_destination_hr = (
            endurance_hr - time_to_destination_hr
        )

        fuel_at_destination_gal = (
            remaining_gal
            - flow_gph * time_to_destination_hr
        )

        if reserve_at_destination_hr < 0.0:
            return FuelAdvice(
                severity="CRITICAL",
                title="Insufficient Fuel to Destination",
                reason=(
                    "Predicted fuel endurance is less than "
                    "the estimated time to destination."
                ),
                action=(
                    "Select a closer suitable airport and "
                    "prepare to divert immediately."
                ),
                endurance_hr=endurance_hr,
                time_to_destination_hr=time_to_destination_hr,
                reserve_at_destination_hr=(
                    reserve_at_destination_hr
                ),
                fuel_at_destination_gal=(
                    fuel_at_destination_gal
                ),
            )

        if (
            reserve_at_destination_hr
            < self.warning_reserve_hr
        ):
            return FuelAdvice(
                severity="WARNING",
                title="Fuel Reserve Warning",
                reason=(
                    "Predicted reserve at destination is below "
                    "the warning threshold."
                ),
                action=(
                    "Divert or land at the nearest suitable "
                    "airport before reserve is exhausted."
                ),
                endurance_hr=endurance_hr,
                time_to_destination_hr=time_to_destination_hr,
                reserve_at_destination_hr=(
                    reserve_at_destination_hr
                ),
                fuel_at_destination_gal=(
                    fuel_at_destination_gal
                ),
            )

        if (
            reserve_at_destination_hr
            < self.caution_reserve_hr
        ):
            return FuelAdvice(
                severity="CAUTION",
                title="Low Fuel Reserve",
                reason=(
                    "Predicted reserve at destination is below "
                    "the caution threshold."
                ),
                action=(
                    "Review nearby airports and consider an "
                    "early fuel stop."
                ),
                endurance_hr=endurance_hr,
                time_to_destination_hr=time_to_destination_hr,
                reserve_at_destination_hr=(
                    reserve_at_destination_hr
                ),
                fuel_at_destination_gal=(
                    fuel_at_destination_gal
                ),
            )

        return FuelAdvice(
            endurance_hr=endurance_hr,
            time_to_destination_hr=time_to_destination_hr,
            reserve_at_destination_hr=(
                reserve_at_destination_hr
            ),
            fuel_at_destination_gal=(
                fuel_at_destination_gal
            ),
        )

    def _endurance_only_advice(
        self,
        endurance_hr: float,
    ) -> FuelAdvice:
        if endurance_hr < self.warning_reserve_hr:
            return FuelAdvice(
                severity="WARNING",
                title="Low Fuel Endurance",
                reason=(
                    "Remaining endurance is below the warning "
                    "threshold."
                ),
                action=(
                    "Land at the nearest suitable airport."
                ),
                endurance_hr=endurance_hr,
            )

        if endurance_hr < self.caution_reserve_hr:
            return FuelAdvice(
                severity="CAUTION",
                title="Fuel Endurance Caution",
                reason=(
                    "Remaining endurance is below the caution "
                    "threshold."
                ),
                action=(
                    "Plan to land soon and verify fuel quantity."
                ),
                endurance_hr=endurance_hr,
            )

        return FuelAdvice(
            endurance_hr=endurance_hr,
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