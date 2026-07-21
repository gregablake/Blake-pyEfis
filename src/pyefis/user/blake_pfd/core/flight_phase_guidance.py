from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseGuidance:
    phase: str
    high_cht: str
    high_oil_temp: str
    cylinder_imbalance: str


PHASE_GUIDANCE = {
    "PARKED": PhaseGuidance(
        phase="PARKED",
        high_cht=(
            "Reduce power to idle and shut down if temperature "
            "continues rising."
        ),
        high_oil_temp=(
            "Reduce power and shut down if oil temperature "
            "continues rising."
        ),
        cylinder_imbalance=(
            "Keep power low and inspect the engine before flight."
        ),
    ),
    "RUNUP": PhaseGuidance(
        phase="RUNUP",
        high_cht=(
            "Reduce power, increase airflow if possible, and "
            "do not take off until temperatures stabilize."
        ),
        high_oil_temp=(
            "Reduce power and do not take off until oil "
            "temperature stabilizes."
        ),
        cylinder_imbalance=(
            "End the runup and investigate the cylinder imbalance "
            "before takeoff."
        ),
    ),
    "TAXI": PhaseGuidance(
        phase="TAXI",
        high_cht=(
            "Reduce power and increase airflow while taxiing if able."
        ),
        high_oil_temp=(
            "Reduce power and increase airflow while taxiing if able."
        ),
        cylinder_imbalance=(
            "Keep power low and evaluate the imbalance before takeoff."
        ),
    ),
    "TAKEOFF": PhaseGuidance(
        phase="TAKEOFF",
        high_cht=(
            "Continue takeoff unless temperatures become critical."
        ),
        high_oil_temp=(
            "Maintain aircraft control and continue monitoring "
            "oil temperature."
        ),
        cylinder_imbalance=(
            "Monitor until reaching a safe altitude."
        ),
    ),
    "CLIMB": PhaseGuidance(
        phase="CLIMB",
        high_cht=(
            "Lower the nose 5–10 kt to improve cooling."
        ),
        high_oil_temp=(
            "Reduce climb angle and increase cooling airflow."
        ),
        cylinder_imbalance=(
            "Monitor the hottest cylinder closely."
        ),
    ),
    "CRUISE": PhaseGuidance(
        phase="CRUISE",
        high_cht=(
            "Lean mixture and reduce power if needed."
        ),
        high_oil_temp=(
            "Reduce power and increase cooling."
        ),
        cylinder_imbalance=(
            "Adjust mixture if appropriate."
        ),
    ),
    "DESCENT": PhaseGuidance(
        phase="DESCENT",
        high_cht=(
            "Temperatures should decrease naturally."
        ),
        high_oil_temp=(
            "Monitor for a cooling trend."
        ),
        cylinder_imbalance=(
            "Continue monitoring."
        ),
    ),
    "LANDING": PhaseGuidance(
        phase="LANDING",
        high_cht=(
            "Maintain aircraft control and complete the landing."
        ),
        high_oil_temp=(
            "Maintain aircraft control and complete the landing."
        ),
        cylinder_imbalance=(
            "Complete the landing and inspect the engine afterward."
        ),
    ),
}