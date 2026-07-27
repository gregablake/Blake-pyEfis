from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    ReachableAirportResult,
)


@dataclass(frozen=True)
class EmergencyAirportAdvice:
    severity: str = "NORMAL"
    title: str = "No Diversion Required"
    message: str = ""
    action: str = ""
    airport_identifier: str | None = None
    bearing_deg: float | None = None
    distance_nm: float | None = None
    arrival_altitude_ft: float | None = None
    safety_margin_ft: float | None = None
    valid: bool = False


class EmergencyAirportAdvisor:
    def __init__(
        self,
        caution_margin_ft: float = 1500.0,
        warning_margin_ft: float = 750.0,
    ) -> None:
        if caution_margin_ft < warning_margin_ft:
            raise ValueError(
                "caution_margin_ft must be greater than "
                "or equal to warning_margin_ft"
            )

        if warning_margin_ft < 0.0:
            raise ValueError(
                "warning_margin_ft must not be negative"
            )

        self.caution_margin_ft = float(
            caution_margin_ft
        )

        self.warning_margin_ft = float(
            warning_margin_ft
        )

    def advise(
        self,
        result: ReachableAirportResult | None,
        emergency_active: bool = False,
    ) -> EmergencyAirportAdvice:
        if not emergency_active:
            return EmergencyAirportAdvice(
                valid=True,
            )

        if result is None or not result.valid:
            return EmergencyAirportAdvice(
                severity="WARNING",
                title="Diversion Data Unavailable",
                message=(
                    "Reachable-airport analysis is unavailable."
                ),
                action=(
                    "Maintain aircraft control and identify "
                    "a suitable landing area visually."
                ),
                valid=False,
            )

        if not result.ranked:
            return EmergencyAirportAdvice(
                severity="CRITICAL",
                title="No Reachable Airport",
                message=(
                    "No airport meets the current glide "
                    "and safety-margin requirements."
                ),
                action=(
                    "Select the best available off-airport "
                    "landing area and complete the emergency "
                    "checklist."
                ),
                valid=True,
            )

        best = result.ranked[0].candidate
        severity = self._severity_for_margin(
            best.safety_margin_ft
        )

        return EmergencyAirportAdvice(
            severity=severity,
            title=f"Best Airport: {best.identifier}",
            message=(
                f"{best.distance_nm:.1f} NM at "
                f"{best.bearing_deg:.0f} degrees. "
                f"Predicted arrival altitude "
                f"{best.arrival_altitude_ft:.0f} ft MSL; "
                f"margin {best.safety_margin_ft:.0f} ft."
            ),
            action=(
                f"Turn toward {best.identifier}, establish "
                "best glide, verify wind and terrain, and "
                "continue evaluating closer landing options."
            ),
            airport_identifier=best.identifier,
            bearing_deg=best.bearing_deg,
            distance_nm=best.distance_nm,
            arrival_altitude_ft=best.arrival_altitude_ft,
            safety_margin_ft=best.safety_margin_ft,
            valid=True,
        )

    def _severity_for_margin(
        self,
        safety_margin_ft: float,
    ) -> str:
        if safety_margin_ft < self.warning_margin_ft:
            return "WARNING"

        if safety_margin_ft < self.caution_margin_ft:
            return "CAUTION"

        return "NORMAL"