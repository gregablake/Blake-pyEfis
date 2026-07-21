from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseGuidance:
    phase: str
    high_cht: str
    high_oil_temp: str
    cylinder_imbalance: str


PHASE_GUIDANCE = {
    "TAKEOFF": PhaseGuidance(
        phase="TAKEOFF",
        high_cht="Continue takeoff unless temperatures become critical.",
        high_oil_temp="Maintain climb while monitoring oil temperature.",
        cylinder_imbalance="Monitor until safe altitude.",
    ),
    "CLIMB": PhaseGuidance(
        phase="CLIMB",
        high_cht="Lower the nose 5–10 kt to improve cooling.",
        high_oil_temp="Reduce climb angle and increase cooling airflow.",
        cylinder_imbalance="Monitor hottest cylinder closely.",
    ),
    "CRUISE": PhaseGuidance(
        phase="CRUISE",
        high_cht="Lean mixture and reduce power if needed.",
        high_oil_temp="Reduce power and increase cooling.",
        cylinder_imbalance="Adjust mixture if appropriate.",
    ),
    "DESCENT": PhaseGuidance(
        phase="DESCENT",
        high_cht="Temperatures should decrease naturally.",
        high_oil_temp="Monitor for cooling trend.",
        cylinder_imbalance="Continue monitoring.",
    ),
}