from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.engine_data import EngineData


@dataclass
class EngineAnalysis:
    summary: str = "Engine operating normally."
    recommendation: str = "Continue normal operation."
    severity: str = "NORMAL"
    hottest_cylinder: int = 0
    hottest_cht_f: float = 0.0
    cht_spread_f: float = 0.0
    egt_spread_f: float = 0.0


class EngineAnalyzer:
    def analyze(self, engine: EngineData, health=None) -> EngineAnalysis:
        cht_values = engine.cht_f or []
        egt_values = engine.egt_f or []

        hottest_cht = max(cht_values) if cht_values else 0.0
        hottest_cylinder = cht_values.index(hottest_cht) + 1 if cht_values else 0
        cht_spread = max(cht_values) - min(cht_values) if cht_values else 0.0
        egt_spread = max(egt_values) - min(egt_values) if egt_values else 0.0

        if engine.oil_pressure_psi <= 15:
            return EngineAnalysis(
                summary="Low oil pressure detected.",
                recommendation="Reduce power and land as soon as practical.",
                severity="CRITICAL",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if engine.oil_temp_f >= 260:
            return EngineAnalysis(
                summary="Oil temperature is above redline.",
                recommendation="Reduce power, increase airspeed, and land soon.",
                severity="CRITICAL",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if hottest_cht >= 450:
            return EngineAnalysis(
                summary=f"CHT cylinder {hottest_cylinder} is above redline.",
                recommendation="Reduce climb angle, enrich mixture, and reduce power.",
                severity="CRITICAL",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if hottest_cht >= 425:
            return EngineAnalysis(
                summary=f"CHT cylinder {hottest_cylinder} is getting hot.",
                recommendation="Increase cooling air and monitor closely.",
                severity="CAUTION",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if egt_spread >= 150:
            return EngineAnalysis(
                summary="EGT spread is elevated.",
                recommendation="Check mixture distribution and monitor cylinders.",
                severity="CAUTION",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if not engine.alternator_online:
            return EngineAnalysis(
                summary="Alternator offline.",
                recommendation="Reduce electrical load and monitor battery voltage.",
                severity="CAUTION",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        score = getattr(health, "health_score", 100) if health is not None else 100

        return EngineAnalysis(
            summary=f"Engine operating normally. Health {score}%.",
            recommendation="Continue normal operation.",
            severity="NORMAL",
            hottest_cylinder=hottest_cylinder,
            hottest_cht_f=hottest_cht,
            cht_spread_f=cht_spread,
            egt_spread_f=egt_spread,
        )