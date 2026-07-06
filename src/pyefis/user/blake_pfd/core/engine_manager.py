from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.engine_data import EngineData


@dataclass
class EngineHealth:
    health_score: int = 100
    cht_max_f: float = 0.0
    cht_spread_f: float = 0.0
    egt_max_f: float = 0.0
    egt_spread_f: float = 0.0
    oil_temp_margin_f: float = 0.0
    oil_pressure_margin_psi: float = 0.0
    status: str = "NORMAL"


class EngineManager:
    def __init__(self) -> None:
        self.health = EngineHealth()

    def update(self, engine: EngineData) -> EngineHealth:
        cht_values = engine.cht_f or []
        egt_values = engine.egt_f or []

        cht_max = max(cht_values) if cht_values else 0.0
        cht_min = min(cht_values) if cht_values else 0.0
        egt_max = max(egt_values) if egt_values else 0.0
        egt_min = min(egt_values) if egt_values else 0.0

        score = 100
        status = "NORMAL"

        if engine.oil_pressure_psi <= 15:
            score -= 40
            status = "CRITICAL"

        if engine.oil_temp_f >= 260:
            score -= 35
            status = "CRITICAL"
        elif engine.oil_temp_f >= 235:
            score -= 15
            status = "CAUTION"

        if cht_max >= 450:
            score -= 35
            status = "CRITICAL"
        elif cht_max >= 425:
            score -= 15
            status = "CAUTION"

        if egt_max >= 1600:
            score -= 20
            status = "CAUTION"

        if not engine.alternator_online:
            score -= 15
            status = "CAUTION"

        score = max(0, min(100, score))

        self.health = EngineHealth(
            health_score=score,
            cht_max_f=cht_max,
            cht_spread_f=cht_max - cht_min if cht_values else 0.0,
            egt_max_f=egt_max,
            egt_spread_f=egt_max - egt_min if egt_values else 0.0,
            oil_temp_margin_f=260.0 - engine.oil_temp_f,
            oil_pressure_margin_psi=engine.oil_pressure_psi - 15.0,
            status=status,
        )

        return self.health