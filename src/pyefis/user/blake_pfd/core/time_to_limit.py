from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.rate_of_change import (
    RateOfChangeResult,
)


@dataclass(frozen=True)
class TimeToLimitResult:
    time_to_limit_s: float | None = None
    approaching_limit: bool = False
    already_exceeded: bool = False
    valid: bool = False


class TimeToLimitCalculator:
    def calculate(
        self,
        current_value: float,
        limit_value: float,
        rate: RateOfChangeResult,
    ) -> TimeToLimitResult:
        current_value = float(current_value)
        limit_value = float(limit_value)

        if current_value >= limit_value:
            return TimeToLimitResult(
                time_to_limit_s=0.0,
                approaching_limit=True,
                already_exceeded=True,
                valid=True,
            )

        if not rate.valid:
            return TimeToLimitResult()

        if rate.rate_per_second <= 0.0:
            return TimeToLimitResult(
                approaching_limit=False,
                already_exceeded=False,
                valid=True,
            )

        remaining = limit_value - current_value
        time_to_limit_s = remaining / rate.rate_per_second

        return TimeToLimitResult(
            time_to_limit_s=time_to_limit_s,
            approaching_limit=True,
            already_exceeded=False,
            valid=True,
        )