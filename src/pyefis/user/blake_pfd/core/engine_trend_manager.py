from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from pyefis.user.blake_pfd.core.rate_of_change import (
    RateOfChangeCalculator,
)
from pyefis.user.blake_pfd.core.rolling_history import (
    RollingHistory,
)


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
    def __init__(
        self,
        history_seconds: float = 10.0,
    ) -> None:
        self.history_seconds = float(history_seconds)

        self.cht_history = RollingHistory(
            window_s=self.history_seconds,
        )

        self.oil_temp_history = RollingHistory(
            window_s=self.history_seconds,
        )

        self.oil_pressure_history = RollingHistory(
            window_s=self.history_seconds,
        )

        self.rate_calculator = RateOfChangeCalculator(
            minimum_samples=2,
            minimum_duration_s=0.001,
        )

    def update(
        self,
        engine,
        sensor_status=None,
    ) -> EngineTrend:
        now = monotonic()

        def channel_usable(status) -> bool:
            return (
                status is None
                or (
                    status.valid
                    and status.fresh
                )
            )

        raw_cht_values = getattr(
            engine,
            "cht_f",
            None,
        ) or []

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

        hottest_cht = (
            float(max(cht_values))
            if cht_values
            else 0.0
        )

        oil_temp_usable = (
            sensor_status is None
            or channel_usable(
                sensor_status.oil_temperature
            )
        )

        oil_pressure_usable = (
            sensor_status is None
            or channel_usable(
                sensor_status.oil_pressure
            )
        )

        oil_temp = (
            float(
                getattr(
                    engine,
                    "oil_temp_f",
                    0.0,
                )
            )
            if oil_temp_usable
            else 0.0
        )

        oil_pressure = (
            float(
                getattr(
                    engine,
                    "oil_pressure_psi",
                    0.0,
                )
            )
            if oil_pressure_usable
            else 0.0
        )

        if cht_values:
            self.cht_history.add(
                value=hottest_cht,
                timestamp_s=now,
            )

        if oil_temp_usable:
            self.oil_temp_history.add(
                value=oil_temp,
                timestamp_s=now,
            )

        if oil_pressure_usable:
            self.oil_pressure_history.add(
                value=oil_pressure,
                timestamp_s=now,
            )

        cht_result = self.rate_calculator.calculate(
            self.cht_history
        )

        oil_temp_result = self.rate_calculator.calculate(
            self.oil_temp_history
        )

        oil_pressure_result = self.rate_calculator.calculate(
            self.oil_pressure_history
        )

        cht_rate = (
            cht_result.rate_per_second
            if cht_result.valid
            else 0.0
        )

        oil_temp_rate = (
            oil_temp_result.rate_per_second
            if oil_temp_result.valid
            else 0.0
        )

        oil_pressure_rate = (
            oil_pressure_result.rate_per_second
            if oil_pressure_result.valid
            else 0.0
        )

        predicted_cht = hottest_cht + (
            cht_rate * 30.0
        )

        predicted_oil_temp = oil_temp + (
            oil_temp_rate * 30.0
        )

        warning = ""

        if predicted_cht >= 440.0:
            warning = "Cylinder temperature increasing."

        if predicted_oil_temp >= 250.0:
            warning = "Oil temperature rising."

        return EngineTrend(
            current_cht=hottest_cht,
            current_oil_temp=oil_temp,
            oil_temp_rate=oil_temp_rate,
            cht_rate=cht_rate,
            oil_pressure_rate=oil_pressure_rate,
            predicted_oil_temp=predicted_oil_temp,
            predicted_cht=predicted_cht,
            warning=warning,
            sample_count=self.cht_history.sample_count,
            history_duration_s=self.cht_history.duration_s,
        )

    def clear(self) -> None:
        self.cht_history.clear()
        self.oil_temp_history.clear()
        self.oil_pressure_history.clear()