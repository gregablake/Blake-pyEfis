from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.rate_of_change import (
    RateOfChangeCalculator,
    RateOfChangeResult,
)
from pyefis.user.blake_pfd.core.rolling_history import (
    RollingHistory,
)
from pyefis.user.blake_pfd.core.time_to_limit import (
    TimeToLimitCalculator,
    TimeToLimitResult,
)


@dataclass(frozen=True)
class SensorTrendPrediction:
    current_value: float | None = None
    rate: RateOfChangeResult = RateOfChangeResult()
    limit: TimeToLimitResult = TimeToLimitResult()
    confidence: float = 0.0
    valid: bool = False


class SensorTrendPredictor:
    def __init__(
        self,
        window_s: float = 60.0,
        minimum_samples: int = 5,
        minimum_duration_s: float = 2.0,
    ) -> None:
        self.history = RollingHistory(
            window_s=window_s,
        )

        self.rate_calculator = RateOfChangeCalculator(
            minimum_samples=minimum_samples,
            minimum_duration_s=minimum_duration_s,
        )

        self.limit_calculator = TimeToLimitCalculator()

        self.minimum_samples = minimum_samples
        self.minimum_duration_s = float(
            minimum_duration_s
        )

    def update(
        self,
        value: float,
        limit_value: float,
        timestamp_s: float | None = None,
    ) -> SensorTrendPrediction:
        self.history.add(
            value=value,
            timestamp_s=timestamp_s,
        )

        rate = self.rate_calculator.calculate(
            self.history
        )

        current = self.history.newest

        if current is None:
            return SensorTrendPrediction()

        limit = self.limit_calculator.calculate(
            current_value=current.value,
            limit_value=limit_value,
            rate=rate,
        )

        confidence = self._confidence(
            sample_count=rate.sample_count,
            duration_s=rate.duration_s,
        )

        return SensorTrendPrediction(
            current_value=current.value,
            rate=rate,
            limit=limit,
            confidence=confidence,
            valid=rate.valid and limit.valid,
        )

    def clear(self) -> None:
        self.history.clear()

    def _confidence(
        self,
        sample_count: int,
        duration_s: float,
    ) -> float:
        sample_confidence = min(
            1.0,
            sample_count / max(
                self.minimum_samples * 4,
                1,
            ),
        )

        duration_confidence = min(
            1.0,
            duration_s / max(
                self.minimum_duration_s * 5.0,
                0.001,
            ),
        )

        return sample_confidence * duration_confidence