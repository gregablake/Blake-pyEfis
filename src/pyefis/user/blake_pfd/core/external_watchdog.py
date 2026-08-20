from __future__ import annotations

import math

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExternalWatchdogState:
    healthy: bool
    stalled: bool
    missing: bool
    invalid: bool
    age_s: float
    message: str


class ExternalWatchdog:
    def __init__(
        self,
        heartbeat_path: str | Path,
        stale_after_s: float = 2.0,
    ) -> None:
        self.heartbeat_path = Path(
            heartbeat_path
        )

        self.stale_after_s = max(
            0.5,
            float(stale_after_s),
        )

    def evaluate(
        self,
        timestamp_s: float,
    ) -> ExternalWatchdogState:
        now_s = float(timestamp_s)

        if not self.heartbeat_path.exists():
            return ExternalWatchdogState(
                healthy=False,
                stalled=True,
                missing=True,
                invalid=False,
                age_s=0.0,
                message="HEARTBEAT MISSING",
            )

        try:
            raw_value = (
                self.heartbeat_path
                .read_text(
                    encoding="utf-8"
                )
                .strip()
            )

            heartbeat_s = float(
                raw_value
            )

        except (
            OSError,
            ValueError,
        ):
            return ExternalWatchdogState(
                healthy=False,
                stalled=True,
                missing=False,
                invalid=True,
                age_s=0.0,
                message="HEARTBEAT INVALID",
            )

        if (
            not math.isfinite(now_s)
            or not math.isfinite(heartbeat_s)
        ):
            return ExternalWatchdogState(
                healthy=False,
                stalled=True,
                missing=False,
                invalid=True,
                age_s=0.0,
                message="HEARTBEAT INVALID",
            )

        age_s = (
            now_s - heartbeat_s
        )

        if age_s < 0.0:
            return ExternalWatchdogState(
                healthy=False,
                stalled=True,
                missing=False,
                invalid=True,
                age_s=0.0,
                message="HEARTBEAT INVALID",
            )

        stalled = (
            age_s
            > self.stale_after_s
        )

        return ExternalWatchdogState(
            healthy=not stalled,
            stalled=stalled,
            missing=False,
            invalid=False,
            age_s=age_s,
            message=(
                "PYEFIS STALLED"
                if stalled
                else "PYEFIS HEALTHY"
            ),
        )