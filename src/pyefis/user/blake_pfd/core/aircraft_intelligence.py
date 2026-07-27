from __future__ import annotations

from dataclasses import dataclass
from pyefis.user.blake_pfd.core.fuel_advisor import (
    FuelAdvisor,
)


@dataclass
class AircraftRecommendation:
    severity: str = "NORMAL"
    title: str = "Normal"
    message: str = "Aircraft systems normal."
    recommendation: str = "Continue normal operation."
    urgency_s: float | None = None
    confidence: float | None = None
    source_priority: int = 0


class AircraftIntelligence:
    _SEVERITY_ORDER = {
        "NORMAL": 0,
        "CAUTION": 1,
        "WARNING": 2,
        "CRITICAL": 3,
    }
    
    def __init__(
        self,
        fuel_advisor: FuelAdvisor | None = None,
    ) -> None:
        self.fuel_advisor = (
            fuel_advisor
            if fuel_advisor is not None
            else FuelAdvisor()
        )

    def analyze(self, aircraft) -> AircraftRecommendation:
        if aircraft is None:
            return AircraftRecommendation()

        engine_state = getattr(
            aircraft,
            "engine_state",
            None,
        )

        recommendations: list[AircraftRecommendation] = []

        if engine_state is not None:
            self._add_engine_analysis(
                recommendations,
                engine_state,
            )

            self._add_cylinder_analysis(
                recommendations,
                engine_state,
            )

            self._add_engine_prediction(
                recommendations,
                engine_state,
            )

            self._add_engine_advice(
                recommendations,
                engine_state,
            )

            self._add_engine_trend(
                recommendations,
                engine_state,
            )

        self._add_fuel_advice(
            recommendations,
            aircraft,
        )

        if not recommendations:
            return AircraftRecommendation()

        return max(
            recommendations,
            key=self._priority_key,
        )

    def _add_engine_analysis(
        self,
        recommendations: list[AircraftRecommendation],
        engine_state,
    ) -> None:
        engine_analysis = getattr(engine_state, "analysis", None)

        if engine_analysis is None:
            return

        severity = getattr(engine_analysis, "severity", "NORMAL")

        if severity == "NORMAL":
            return

        title = "Engine" if severity in {"WARNING", "CRITICAL"} else "Engine Caution"

        recommendations.append(
            AircraftRecommendation(
                severity=severity,
                title=title,
                message=getattr(
                    engine_analysis,
                    "summary",
                    "Engine issue detected.",
                ),
                recommendation=getattr(
                    engine_analysis,
                    "recommendation",
                    "Monitor engine instruments.",
                ),
            )
        )

    def _add_cylinder_analysis(
        self,
        recommendations: list[AircraftRecommendation],
        engine_state,
    ) -> None:
        cylinders = getattr(engine_state, "cylinders", None)

        if cylinders is None:
            return

        if not getattr(cylinders, "imbalance_detected", False):
            return

        recommendations.append(
            AircraftRecommendation(
                severity="CAUTION",
                title="Cylinder Balance",
                message=getattr(
                    cylinders,
                    "message",
                    "Cylinder imbalance detected.",
                ),
                recommendation=(
                    "Monitor CHT and EGT spread and consider mixture "
                    "or cooling adjustment."
                ),
            )
        )

    def _add_engine_prediction(
        self,
        recommendations: list[AircraftRecommendation],
        engine_state,
    ) -> None:
        prediction = getattr(engine_state, "prediction", None)

        if prediction is None:
            return

        severity = getattr(prediction, "severity", "NORMAL")

        if severity == "NORMAL":
            return

        times = [
            value
            for value in (
                getattr(prediction, "time_to_cht_limit_s", None),
                getattr(prediction, "time_to_oil_temp_limit_s", None),
            )
            if value is not None
        ]

        urgency_s = min(times) if times else None
        confidence = getattr(prediction, "confidence", None)

        recommendations.append(
            AircraftRecommendation(
                severity=severity,
                title="Predicted Engine Limit",
                message=getattr(
                    prediction,
                    "message",
                    "Engine limit exceedance predicted.",
                ),
                recommendation=(
                    "Adjust power, mixture, airspeed, or climb rate "
                    "before the limit is reached."
                ),
                urgency_s=urgency_s,
                confidence=confidence,
                source_priority=1,
            )
        )

    def _add_engine_advice(
        self,
        recommendations: list[AircraftRecommendation],
        engine_state,
    ) -> None:
        advice = getattr(engine_state, "advice", None)

        if advice is None:
            return

        severity = getattr(advice, "severity", "NORMAL")

        if severity == "NORMAL":
            return
        recommendations.append(
            AircraftRecommendation(
                severity=severity,
                title=getattr(
                    advice,
                    "title",
                    "Engine Advisor",
                ),
                message=getattr(
                    advice,
                    "reason",
                    "Engine advisory condition detected.",
                ),
                recommendation=getattr(
                    advice,
                    "action",
                    "Monitor engine instruments.",
                ),
                confidence=getattr(
                    advice,
                    "confidence",
                    None,
                ),
                urgency_s=getattr(
                    advice,
                    "urgency_s",
                    None,
                ),
                source_priority=2,
            )
        )

    def _add_engine_trend(
        self,
        recommendations: list[AircraftRecommendation],
        engine_state,
    ) -> None:
        trend = getattr(engine_state, "trend", None)

        if trend is None:
            return

        warning = getattr(trend, "warning", "")

        if not warning:
            return

        recommendations.append(
            AircraftRecommendation(
                severity="CAUTION",
                title="Engine Trend",
                message=warning,
                recommendation=(
                    "Adjust power, mixture, airspeed, or climb rate "
                    "before limits are reached."
                ),
            )
        )
        
    def _add_fuel_advice(
        self,
        recommendations: list[AircraftRecommendation],
        aircraft,
    ) -> None:
        fuel_state = getattr(
            aircraft,
            "fuel",
            None,
        )

        navigation_state = getattr(
            aircraft,
            "navigation",
            None,
        )

        ground_speed_kt = getattr(
            aircraft,
            "ground_speed_kt",
            0.0,
        )

        advice = self.fuel_advisor.advise(
            fuel_state=fuel_state,
            navigation_state=navigation_state,
            ground_speed_kt=ground_speed_kt,
        )

        if advice.severity == "NORMAL":
            return

        urgency_s = None

        if (
            advice.reserve_at_destination_hr is not None
            and advice.reserve_at_destination_hr >= 0.0
        ):
            urgency_s = (
                advice.reserve_at_destination_hr
                * 3600.0
            )

        recommendations.append(
            AircraftRecommendation(
                severity=advice.severity,
                title=advice.title,
                message=advice.reason,
                recommendation=advice.action,
                urgency_s=urgency_s,
                confidence=1.0,
                source_priority=3,
            )
        )

    def _priority_key(
        self,
        recommendation: AircraftRecommendation,
    ) -> tuple[int, int, float]:
        severity_rank = self._SEVERITY_ORDER.get(
            recommendation.severity,
            0,
        )

        source_rank = recommendation.source_priority

        urgency_rank = (
            -recommendation.urgency_s
            if recommendation.urgency_s is not None
            else float("-inf")
        )

        return severity_rank, source_rank, urgency_rank
