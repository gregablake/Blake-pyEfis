from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.engine_knowledge import (
    ENGINE_SCENARIOS,
    EngineScenario,
)
from pyefis.user.blake_pfd.core.flight_phase_guidance import (
    PHASE_GUIDANCE,
)


@dataclass
class EngineAdvice:
    severity: str = "NORMAL"
    title: str = "Engine Normal"
    reason: str = "No abnormal engine condition detected."
    action: str = "Continue normal operation."
    confidence: float = 0.0
    urgency_s: float | None = None


class EngineAdvisor:
    def advise(
        self,
        engine_state,
        flight_state=None,
    ) -> EngineAdvice:
        if engine_state is None:
            return EngineAdvice()

        prediction = getattr(
            engine_state,
            "prediction",
            None,
        )

        cylinders = getattr(
            engine_state,
            "cylinders",
            None,
        )

        health = getattr(
            engine_state,
            "health",
            None,
        )

        data = getattr(
            engine_state,
            "data",
            None,
        )

        # A current critical condition must always beat
        # a future predicted condition.
        health_advice = self._health_advice(
            health,
            data,
        )

        if (
            health_advice is not None
            and health_advice.severity == "CRITICAL"
        ):
            return health_advice

        prediction_advice = self._prediction_advice(
            prediction,
            flight_state,
        )

        if prediction_advice is not None:
            return prediction_advice

        cylinder_advice = self._cylinder_advice(
            cylinders,
            flight_state,
        )

        if cylinder_advice is not None:
            return cylinder_advice

        if health_advice is not None:
            return health_advice

        return EngineAdvice()

    def _prediction_advice(
        self,
        prediction,
        flight_state,
    ) -> EngineAdvice | None:
        if prediction is None:
            return None

        severity = getattr(
            prediction,
            "severity",
            "NORMAL",
        )

        if severity == "NORMAL":
            return None

        message = getattr(
            prediction,
            "message",
            "Engine limit predicted.",
        )

        parameter = getattr(
            prediction,
            "parameter",
            None,
        )

        # Backward compatibility for older prediction objects
        # that do not yet contain the structured parameter field.
        if parameter is None:
            upper_message = message.upper()

            if "CHT" in upper_message:
                parameter = "CHT"
            elif "OIL" in upper_message:
                parameter = "OIL_TEMP"

        confidence = float(
            getattr(
                prediction,
                "confidence",
                0.0,
            )
        )
        
        times = [
            value
            for value in (
                getattr(
                    prediction,
                    "time_to_cht_limit_s",
                    None,
                ),
                getattr(
                    prediction,
                    "time_to_oil_temp_limit_s",
                    None,
                ),
            )
            if value is not None
        ]

        urgency_s = min(times) if times else None

        phase = getattr(
            flight_state,
            "phase",
            "UNKNOWN",
        )

        phase_guidance = PHASE_GUIDANCE.get(
            phase
        )

        if parameter == "CHT":
            return self._cht_prediction_advice(
                severity=severity,
                confidence=confidence,
                urgency_s=urgency_s,
                phase=phase,
                phase_guidance=phase_guidance,
            )

        if parameter == "OIL_TEMP":
            return self._oil_temperature_prediction_advice(
                severity=severity,
                confidence=confidence,
                urgency_s=urgency_s,
                phase_guidance=phase_guidance,
            )

        return EngineAdvice(
            severity=severity,
            title="Predicted Engine Limit",
            reason=message,
            action=(
                "Adjust power, mixture, airspeed, or climb rate "
                "before the predicted limit is reached."
            ),
            confidence=confidence,
            urgency_s=urgency_s,
        )

    def _cht_prediction_advice(
        self,
        severity: str,
        confidence: float,
        urgency_s: float | None,
        phase: str,
        phase_guidance,
    ) -> EngineAdvice:
        scenario = self._scenario(
            "High CHT During Climb"
        )

        if phase in {"TAKEOFF", "CLIMB"}:
            reason = self._join_items(
                scenario.likely_causes,
                fallback=(
                    "Cylinder temperature is rising during a "
                    "high-power flight phase."
                ),
            )

            knowledge_action = self._join_items(
                scenario.recommended_actions,
                fallback=(
                    "Increase airspeed, reduce climb angle, "
                    "and reduce power if necessary."
                ),
            )

            if phase_guidance is not None:
                action = (
                    f"{phase_guidance.high_cht} "
                    f"{knowledge_action}"
                )
            else:
                action = knowledge_action

        else:
            reason = (
                "Cylinder temperature is approaching its limit. "
                + self._join_items(
                    scenario.likely_causes,
                    fallback=(
                        "Cooling airflow may be insufficient."
                    ),
                )
            )

            knowledge_action = (
                "Reduce power and monitor mixture "
                "and cooling airflow."
            )

            if phase_guidance is not None:
                action = (
                    f"{phase_guidance.high_cht} "
                    f"{knowledge_action}"
                )
            else:
                action = knowledge_action

        return EngineAdvice(
            severity=severity,
            title="CHT Cooling Advisor",
            reason=reason,
            action=action,
            confidence=confidence,
            urgency_s=urgency_s,
        )

    def _oil_temperature_prediction_advice(
        self,
        severity: str,
        confidence: float,
        urgency_s: float | None,
        phase_guidance,
    ) -> EngineAdvice:
        scenario = self._scenario(
            "High Oil Temperature"
        )

        reason = self._join_items(
            scenario.likely_causes,
            fallback=(
                "Oil temperature is predicted to reach its limit."
            ),
        )

        action = self._join_items(
            scenario.recommended_actions,
            fallback=(
                "Reduce power, increase cooling airflow, "
                "and level temporarily."
            ),
        )

        if phase_guidance is not None:
            action = (
                f"{phase_guidance.high_oil_temp} "
                f"{action}"
            )

        return EngineAdvice(
            severity=severity,
            title="Oil Temperature Advisor",
            reason=reason,
            action=action,
            confidence=confidence,
            urgency_s=urgency_s,
        )

    def _cylinder_advice(
        self,
        cylinders,
        flight_state,
    ) -> EngineAdvice | None:
        if cylinders is None:
            return None

        if not getattr(
            cylinders,
            "imbalance_detected",
            False,
        ):
            return None

        scenario = self._scenario(
            "Cylinder Imbalance"
        )

        phase = getattr(
            flight_state,
            "phase",
            "UNKNOWN",
        )

        phase_guidance = PHASE_GUIDANCE.get(
            phase
        )

        hottest_cylinder = getattr(
            cylinders,
            "hottest_cylinder",
            0,
        )

        cht_spread = getattr(
            cylinders,
            "cht_spread_f",
            0.0,
        )

        egt_spread = getattr(
            cylinders,
            "egt_spread_f",
            0.0,
        )

        likely_causes = self._join_items(
            scenario.likely_causes,
            fallback=(
                "Cooling or mixture imbalance may be present."
            ),
        )

        recommended_actions = self._join_items(
            scenario.recommended_actions,
            fallback=(
                "Monitor the hottest cylinder, verify mixture balance, "
                "and inspect cooling airflow if the spread persists."
            ),
        )

        if phase_guidance is not None:
            recommended_actions = (
                f"{phase_guidance.cylinder_imbalance} "
                f"{recommended_actions}"
            )

        return EngineAdvice(
            severity="CAUTION",
            title="Cylinder Balance Advisor",
            reason=(
                f"Cylinder {hottest_cylinder} is hottest. "
                f"CHT spread {cht_spread:.0f}F, "
                f"EGT spread {egt_spread:.0f}F. "
                f"Likely causes: {likely_causes}"
            ),
            action=recommended_actions,
            confidence=0.8,
        )

    def _health_advice(
        self,
        health,
        data,
    ) -> EngineAdvice | None:
        if health is None:
            return None

        status = getattr(
            health,
            "status",
            "NORMAL",
        )

        if status == "NORMAL":
            return None

        if data is not None:
            oil_pressure = getattr(
                data,
                "oil_pressure_psi",
                0.0,
            )

            if oil_pressure <= 15.0:
                return EngineAdvice(
                    severity="CRITICAL",
                    title="Oil Pressure Advisor",
                    reason=(
                        "Oil pressure is below the critical threshold."
                    ),
                    action=(
                        "Reduce power and prepare for immediate landing. "
                        "Shut down the engine if pressure is lost."
                    ),
                    confidence=1.0,
                )

        return EngineAdvice(
            severity=status,
            title="Engine Health Advisor",
            reason=(
                f"Engine health status is {status}. "
                f"Health score: "
                f"{getattr(health, 'health_score', 0)}%."
            ),
            action=(
                "Review engine instruments and respond to "
                "the active warning."
            ),
            confidence=0.9,
        )

    @staticmethod
    def _scenario(
        name: str,
    ) -> EngineScenario:
        for scenario in ENGINE_SCENARIOS:
            if scenario.name == name:
                return scenario

        raise ValueError(
            f"Engine knowledge scenario not found: {name}"
        )

    @staticmethod
    def _join_items(
        items: tuple[str, ...],
        fallback: str,
    ) -> str:
        if not items:
            return fallback

        return "; ".join(items) + "."