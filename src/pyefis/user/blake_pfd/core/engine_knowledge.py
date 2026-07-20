from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineScenario:
    name: str
    symptoms: tuple[str, ...]
    likely_causes: tuple[str, ...]
    recommended_actions: tuple[str, ...]


ENGINE_SCENARIOS = (
    EngineScenario(
        name="High CHT During Climb",
        symptoms=(
            "CHT rising",
            "High power",
            "Low airspeed",
        ),
        likely_causes=(
            "Cooling airflow insufficient",
            "Climb angle too steep",
        ),
        recommended_actions=(
            "Increase airspeed",
            "Reduce climb angle",
            "Reduce power if necessary",
        ),
    ),
    EngineScenario(
        name="High Oil Temperature",
        symptoms=(
            "Oil temperature rising",
        ),
        likely_causes=(
            "High engine load",
            "Reduced cooling",
        ),
        recommended_actions=(
            "Reduce power",
            "Increase cooling airflow",
            "Leveling temporarily",
        ),
    ),
    EngineScenario(
        name="Cylinder Imbalance",
        symptoms=(
            "Large CHT spread",
            "Large EGT spread",
        ),
        likely_causes=(
            "Cooling imbalance",
            "Mixture imbalance",
        ),
        recommended_actions=(
            "Monitor hottest cylinder",
            "Verify mixture balance",
            "Check for blockage in cooling airflow",
            "Inspect baffling after landing to ensure no blockages",
        ),
    ),
)