from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.rolling_history import (
    RollingHistory,
)


@dataclass(frozen=True)
class RateOfChangeResult:
    rate_per_second: float = 0.0
    sample_count: int = 0
    duration_s: float = 0.0
    start_value: float | None = None
    end_value: float | None = None
    valid: bool = False


class RateOfChangeCalculator:
    def __init__(
        self,
        minimum_samples: int = 2,
        minimum_duration_s: float = 1.0,
    ) -> None:
        if minimum_samples < 2:
            raise ValueError(
                "minimum_samples must be at least 2"
            )

        if minimum_duration_s <= 0:
            raise ValueError(
                "minimum_duration_s must be greater than zero"
            )

        self.minimum_samples = minimum_samples
        self.minimum_duration_s = float(
            minimum_duration_s
        )

    def calculate(
        self,
        history: RollingHistory,
    ) -> RateOfChangeResult:
        samples = history.samples
        sample_count = len(samples)
        duration_s = history.duration_s

        if sample_count == 0:
            return RateOfChangeResult()

        start_value = samples[0].value
        end_value = samples[-1].value

        if sample_count < self.minimum_samples:
            return RateOfChangeResult(
                sample_count=sample_count,
                duration_s=duration_s,
                start_value=start_value,
                end_value=end_value,
            )

        if duration_s < self.minimum_duration_s:
            return RateOfChangeResult(
                sample_count=sample_count,
                duration_s=duration_s,
                start_value=start_value,
                end_value=end_value,
            )

        rate_per_second = (
            end_value - start_value
        ) / duration_s

        return RateOfChangeResult(
            rate_per_second=rate_per_second,
            sample_count=sample_count,
            duration_s=duration_s,
            start_value=start_value,
            end_value=end_value,
            valid=True,
        )