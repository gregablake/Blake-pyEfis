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
    _SEVERITY_ORDER = {
        "NORMAL": 0,
        "CAUTION": 1,
        "CRITICAL": 2,
    }

    def __init__(self) -> None:
        self.health = EngineHealth()

    @classmethod
    def _raise_status(cls, current: str, new: str) -> str:
        if cls._SEVERITY_ORDER[new] > cls._SEVERITY_ORDER[current]:
            return new

        return current

    def update(
        self,
        engine: EngineData,
        sensor_status=None,
    ) -> EngineHealth:
        def channel_usable(status) -> bool:
            return (
                status is None
                or (
                    status.valid
                    and status.fresh
                )
            )

        raw_cht_values = engine.cht_f or []
        raw_egt_values = engine.egt_f or []

        cht_values = [
            float(value)
            for index, value in enumerate(
                raw_cht_values
            )
            if (
                sensor_status is None
                or (
                    index < len(sensor_status.cht)
                    and channel_usable(
                        sensor_status.cht[index]
                    )
                )
            )
        ]

        egt_values = [
            float(value)
            for index, value in enumerate(
                raw_egt_values
            )
            if (
                sensor_status is None
                or (
                    index < len(sensor_status.egt)
                    and channel_usable(
                        sensor_status.egt[index]
                    )
                )
            )
        ]

        cht_max = max(cht_values) if cht_values else 0.0
        cht_min = min(cht_values) if cht_values else 0.0
        egt_max = max(egt_values) if egt_values else 0.0
        egt_min = min(egt_values) if egt_values else 0.0

        oil_pressure_usable = (
            sensor_status is None
            or channel_usable(
                sensor_status.oil_pressure
            )
        )

        oil_temperature_usable = (
            sensor_status is None
            or channel_usable(
                sensor_status.oil_temperature
            )
        )

        score = 100
        status = "NORMAL"

        if (
            oil_pressure_usable
            and engine.oil_pressure_psi <= 15
        ):
            score -= 40
            status = self._raise_status(status, "CRITICAL")

        if (
            oil_temperature_usable
            and engine.oil_temp_f >= 260
        ):
            score -= 35
            status = self._raise_status(status, "CRITICAL")
        elif (
            oil_temperature_usable
            and engine.oil_temp_f >= 235
        ):
            score -= 15
            status = self._raise_status(status, "CAUTION")

        if cht_max >= 450:
            score -= 35
            status = self._raise_status(status, "CRITICAL")
        elif cht_max >= 425:
            score -= 15
            status = self._raise_status(status, "CAUTION")

        if egt_max >= 1600:
            score -= 20
            status = self._raise_status(status, "CAUTION")

        if not engine.alternator_online:
            score -= 15
            status = self._raise_status(status, "CAUTION")

        score = max(0, min(100, score))

        self.health = EngineHealth(
            health_score=score,
            cht_max_f=cht_max,
            cht_spread_f=cht_max - cht_min if cht_values else 0.0,
            egt_max_f=egt_max,
            egt_spread_f=egt_max - egt_min if egt_values else 0.0,
            oil_temp_margin_f=(
                260.0 - engine.oil_temp_f
                if oil_temperature_usable
                else 0.0
            ),
            oil_pressure_margin_psi=(
                engine.oil_pressure_psi - 15.0
                if oil_pressure_usable
                else 0.0
            ),
            status=status,
        )

        return self.health