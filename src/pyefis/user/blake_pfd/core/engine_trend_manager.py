from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class EngineTrend:
    oil_temp_rate: float = 0.0
    cht_rate: float = 0.0
    oil_pressure_rate: float = 0.0

    predicted_oil_temp: float = 0.0
    predicted_cht: float = 0.0

    warning: str = ""


class EngineTrendManager:
    def __init__(self):
        self.oil_temp = deque(maxlen=60)
        self.cht = deque(maxlen=60)
        self.oil_pressure = deque(maxlen=60)

    def update(self, engine):

        self.oil_temp.append(engine.oil_temp_f)

        hottest = max(engine.cht_f) if engine.cht_f else 0
        self.cht.append(hottest)

        self.oil_pressure.append(engine.oil_pressure_psi)

        trend = EngineTrend()

        if len(self.oil_temp) >= 10:

            trend.oil_temp_rate = (
                self.oil_temp[-1] - self.oil_temp[0]
            ) / len(self.oil_temp)

            trend.predicted_oil_temp = (
                self.oil_temp[-1]
                + trend.oil_temp_rate * 30
            )

        if len(self.cht) >= 10:

            trend.cht_rate = (
                self.cht[-1] - self.cht[0]
            ) / len(self.cht)

            trend.predicted_cht = (
                self.cht[-1]
                + trend.cht_rate * 30
            )

        if trend.predicted_oil_temp >= 250:
            trend.warning = "Oil temperature rising."

        if trend.predicted_cht >= 440:
            trend.warning = "Cylinder temperature increasing."

        return trend