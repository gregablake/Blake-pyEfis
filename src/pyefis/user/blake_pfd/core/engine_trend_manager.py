from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass
class EngineTrend:
    current_cht: float = 0.0
    current_oil_temp: float = 0.0

    oil_temp_rate: float = 0.0
    cht_rate: float = 0.0
    oil_pressure_rate: float = 0.0

    predicted_oil_temp: float = 0.0
    predicted_cht: float = 0.0

    warning: str = ""
    sample_count: int = 0
    history_duration_s: float = 0.0

class EngineTrendManager:
    def __init__(self, history_seconds: float = 10.0) -> None:
        self.history_seconds = history_seconds

        self.cht_history: deque[tuple[float, float]] = deque()
        self.oil_temp_history: deque[tuple[float, float]] = deque()
        self.oil_pressure_history: deque[tuple[float, float]] = deque()

    def update(self, engine) -> EngineTrend:
        now = monotonic()

        cht_values = getattr(engine, "cht_f", None) or []
        hottest_cht = max(cht_values) if cht_values else 0.0

        oil_temp = float(getattr(engine, "oil_temp_f", 0.0))
        oil_pressure = float(
            getattr(engine, "oil_pressure_psi", 0.0)
        )

        self.cht_history.append((now, hottest_cht))
        self.oil_temp_history.append((now, oil_temp))
        self.oil_pressure_history.append((now, oil_pressure))

        self._trim_history(self.cht_history, now)
        self._trim_history(self.oil_temp_history, now)
        self._trim_history(self.oil_pressure_history, now)

        cht_rate = self._rate_per_second(self.cht_history)
        oil_temp_rate = self._rate_per_second(
            self.oil_temp_history
        )
        oil_pressure_rate = self._rate_per_second(
            self.oil_pressure_history
        )

        predicted_cht = hottest_cht + (cht_rate * 30.0)
        predicted_oil_temp = oil_temp + (
            oil_temp_rate * 30.0
        )

        warning = ""

        if predicted_cht >= 440.0:
            warning = "Cylinder temperature increasing."

        if predicted_oil_temp >= 250.0:
            warning = "Oil temperature rising."
            
        history_duration_s = self._history_duration(self.cht_history)

        # Calculate the duration of the history

        return EngineTrend(
            current_cht=hottest_cht,
            current_oil_temp=oil_temp,
            oil_temp_rate=oil_temp_rate,
            cht_rate=cht_rate,
            oil_pressure_rate=oil_pressure_rate,
            predicted_oil_temp=predicted_oil_temp,
            predicted_cht=predicted_cht,
            warning=warning,
            sample_count=len(self.cht_history),
            history_duration_s=history_duration_s,
        )

    def _trim_history(
        self,
        history: deque[tuple[float, float]],
        now: float,
    ) -> None:
        cutoff = now - self.history_seconds

        while history and history[0][0] < cutoff:
            history.popleft()

    @staticmethod
    def _rate_per_second(
        history: deque[tuple[float, float]],
    ) -> float:
        if len(history) < 2:
            return 0.0

        first_time, first_value = history[0]
        last_time, last_value = history[-1]

        elapsed = last_time - first_time

        if elapsed <= 0.0:
            return 0.0

        return (last_value - first_value) / elapsed
    
    @staticmethod
    def _history_duration(
        history: deque[tuple[float, float]],
    ) -> float:
        if len(history) < 2:
            return 0.0

        return max(0.0, history[-1][0] - history[0][0])