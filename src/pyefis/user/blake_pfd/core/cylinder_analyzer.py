from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.engine_data import EngineData


@dataclass
class CylinderAnalysis:
    hottest_cylinder: int = 0
    hottest_cht_f: float = 0.0
    cht_spread_f: float = 0.0
    egt_spread_f: float = 0.0
    imbalance_detected: bool = False
    message: str = "Cylinders balanced."


class CylinderAnalyzer:
    def analyze(self, engine: EngineData) -> CylinderAnalysis:
        cht_values = engine.cht_f or []
        egt_values = engine.egt_f or []

        hottest_cht = max(cht_values) if cht_values else 0.0
        hottest_cylinder = cht_values.index(hottest_cht) + 1 if cht_values else 0
        cht_spread = max(cht_values) - min(cht_values) if cht_values else 0.0
        egt_spread = max(egt_values) - min(egt_values) if egt_values else 0.0

        imbalance = cht_spread >= 60.0 or egt_spread >= 150.0

        if imbalance:
            message = (
                f"Cylinder imbalance: CHT spread {cht_spread:.0f}F, "
                f"EGT spread {egt_spread:.0f}F."
            )
        else:
            message = "Cylinders balanced."

        return CylinderAnalysis(
            hottest_cylinder=hottest_cylinder,
            hottest_cht_f=hottest_cht,
            cht_spread_f=cht_spread,
            egt_spread_f=egt_spread,
            imbalance_detected=imbalance,
            message=message,
        )