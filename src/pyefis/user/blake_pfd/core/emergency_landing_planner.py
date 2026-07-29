from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from pyefis.user.blake_pfd.core.emergency_airport_advisor import (
    EmergencyAirportAdvice,
)


@dataclass(frozen=True)
class EmergencyLandingPlan:
    active: bool = False
    airport_identifier: str | None = None
    distance_nm: float | None = None
    bearing_deg: float | None = None
    estimated_time_sec: float | None = None
    arrival_altitude_ft: float | None = None
    safety_margin_ft: float | None = None
    recommended_speed_kt: float | None = None
    checklist_name: str = ""
    instruction: str = ""
    valid: bool = False


class EmergencyLandingPlanner:
    def __init__(
        self,
        best_glide_speed_kt: float = 80.0,
        checklist_name: str = "ENGINE_FAILURE",
    ) -> None:
        self.best_glide_speed_kt = self._require_positive(
            best_glide_speed_kt,
            "best_glide_speed_kt",
        )

        self.checklist_name = str(checklist_name).strip()

        if not self.checklist_name:
            raise ValueError(
                "checklist_name must not be empty"
            )

    def create_plan(
        self,
        *,
        advice: EmergencyAirportAdvice | None,
        emergency_active: bool,
        ground_speed_kt=None,
    ) -> EmergencyLandingPlan:
        if not emergency_active:
            return EmergencyLandingPlan(
                valid=True,
            )

        if advice is None or not advice.valid:
            return EmergencyLandingPlan(
                active=True,
                recommended_speed_kt=(
                    self.best_glide_speed_kt
                ),
                checklist_name=self.checklist_name,
                instruction=(
                    "ESTABLISH BEST GLIDE AND SELECT "
                    "A SUITABLE LANDING AREA"
                ),
                valid=False,
            )

        if (
            advice.airport_identifier is None
            or advice.distance_nm is None
            or advice.bearing_deg is None
        ):
            return EmergencyLandingPlan(
                active=True,
                recommended_speed_kt=(
                    self.best_glide_speed_kt
                ),
                checklist_name=self.checklist_name,
                instruction=(
                    "NO REACHABLE AIRPORT. SELECT THE "
                    "BEST AVAILABLE LANDING AREA"
                ),
                valid=False,
            )

        distance_nm = self._safe_nonnegative(
            advice.distance_nm
        )

        bearing_deg = self._safe_angle(
            advice.bearing_deg
        )

        if distance_nm is None or bearing_deg is None:
            return EmergencyLandingPlan(
                active=True,
                recommended_speed_kt=(
                    self.best_glide_speed_kt
                ),
                checklist_name=self.checklist_name,
                instruction=(
                    "DIVERSION DATA INVALID. ESTABLISH "
                    "BEST GLIDE"
                ),
                valid=False,
            )

        safe_ground_speed_kt = self._safe_positive(
            ground_speed_kt
        )

        if safe_ground_speed_kt is None:
            safe_ground_speed_kt = (
                self.best_glide_speed_kt
            )

        estimated_time_sec = (
            distance_nm
            / safe_ground_speed_kt
            * 3600.0
        )

        airport_identifier = str(
            advice.airport_identifier
        ).strip().upper()

        instruction = (
            f"TURN TOWARD {airport_identifier} "
            f"COURSE {bearing_deg:.0f} DEGREES. "
            f"MAINTAIN {self.best_glide_speed_kt:.0f} KT."
        )

        return EmergencyLandingPlan(
            active=True,
            airport_identifier=airport_identifier,
            distance_nm=distance_nm,
            bearing_deg=bearing_deg,
            estimated_time_sec=estimated_time_sec,
            arrival_altitude_ft=(
                advice.arrival_altitude_ft
            ),
            safety_margin_ft=(
                advice.safety_margin_ft
            ),
            recommended_speed_kt=(
                self.best_glide_speed_kt
            ),
            checklist_name=self.checklist_name,
            instruction=instruction,
            valid=True,
        )

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

        if number < 0.0:
            return None

        return number

    @staticmethod
    def _safe_positive(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number) or number <= 0.0:
            return None

        return number

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

    @staticmethod
    def _require_positive(
        value,
        name: str,
    ) -> float:
        number = float(value)

        if not isfinite(number) or number <= 0.0:
            raise ValueError(
                f"{name} must be finite and positive"
            )

        return number