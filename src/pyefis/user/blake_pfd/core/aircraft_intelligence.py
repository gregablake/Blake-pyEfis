from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AircraftRecommendation:
    severity: str = "NORMAL"
    title: str = "Normal"
    message: str = "Aircraft systems normal."
    recommendation: str = "Continue normal operation."


class AircraftIntelligence:
    def analyze(self, aircraft) -> AircraftRecommendation:
        if aircraft is None:
            return AircraftRecommendation()

        engine_state = getattr(aircraft, "engine_state", None)

        if engine_state is not None:
            engine_analysis = getattr(engine_state, "analysis", None)

            if engine_analysis is not None:
                severity = getattr(engine_analysis, "severity", "NORMAL")

                if severity in {"WARNING", "CRITICAL"}:
                    return AircraftRecommendation(
                        severity=severity,
                        title="Engine",
                        message=getattr(engine_analysis, "summary", "Engine issue detected."),
                        recommendation=getattr(
                            engine_analysis,
                            "recommendation",
                            "Monitor engine instruments.",
                        ),
                    )

                if severity == "CAUTION":
                    return AircraftRecommendation(
                        severity="CAUTION",
                        title="Engine Caution",
                        message=getattr(engine_analysis, "summary", "Engine caution detected."),
                        recommendation=getattr(
                            engine_analysis,
                            "recommendation",
                            "Monitor engine instruments.",
                        ),
                    )

            cylinders = getattr(engine_state, "cylinders", None)

            if cylinders is not None and getattr(cylinders, "imbalance_detected", False):
                return AircraftRecommendation(
                    severity="CAUTION",
                    title="Cylinder Balance",
                    message=getattr(cylinders, "message", "Cylinder imbalance detected."),
                    recommendation="Monitor CHT/EGT spread and consider mixture or cooling adjustment.",
                )
                
            prediction = getattr(engine_state, "prediction", None)

            if prediction is not None:
                prediction_severity = getattr(
                    prediction,
                    "severity",
                    "NORMAL",
                )

                if prediction_severity != "NORMAL":
                    return AircraftRecommendation(
                    severity=prediction_severity,
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
                )

            trend = getattr(engine_state, "trend", None)

            if trend is not None and getattr(trend, "warning", ""):
                return AircraftRecommendation(
                    severity="CAUTION",
                    title="Engine Trend",
                    message=getattr(trend, "warning", "Engine trend warning."),
                    recommendation="Adjust power, mixture, airspeed, or climb rate before limits are reached.",
                )

        return AircraftRecommendation()