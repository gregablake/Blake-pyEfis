from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataFreshnessState:
    fresh: bool
    stale: bool
    age_s: float
    message: str


class DataFreshnessMonitor:
    def __init__(
        self,
        stale_after_s: float = 1.0,
    ) -> None:
        self.stale_after_s = max(
            0.1,
            float(stale_after_s),
        )

        self.last_update_s: float | None = None

    def mark_update(
        self,
        timestamp_s: float,
    ) -> None:
        self.last_update_s = float(
            timestamp_s
        )

    def evaluate(
        self,
        timestamp_s: float,
    ) -> DataFreshnessState:
        now_s = float(timestamp_s)

        if self.last_update_s is None:
            return DataFreshnessState(
                fresh=False,
                stale=True,
                age_s=0.0,
                message="NO SENSOR DATA",
            )

        age_s = max(
            0.0,
            now_s - self.last_update_s,
        )

        stale = (
            age_s
            > self.stale_after_s
        )

        return DataFreshnessState(
            fresh=not stale,
            stale=stale,
            age_s=age_s,
            message=(
                "SENSOR DATA STALE"
                if stale
                else "DATA FRESH"
            ),
        )