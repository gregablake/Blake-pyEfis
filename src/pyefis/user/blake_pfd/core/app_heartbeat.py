from __future__ import annotations

import math

from dataclasses import dataclass


@dataclass(frozen=True)
class AppHeartbeatState:
    healthy: bool
    stalled: bool
    age_s: float
    message: str


class AppHeartbeat:
    def __init__(
        self,
        stall_after_s: float = 2.0,
    ) -> None:
        self.stall_after_s = max(
            0.5,
            float(stall_after_s),
        )

        self.last_beat_s: float | None = None

    def beat(
        self,
        timestamp_s: float,
    ) -> None:
        self.last_beat_s = float(
            timestamp_s
        )

    def evaluate(
        self,
        timestamp_s: float,
    ) -> AppHeartbeatState:
        now_s = float(timestamp_s)

        if self.last_beat_s is None:
            return AppHeartbeatState(
                healthy=False,
                stalled=True,
                age_s=0.0,
                message="APP HEARTBEAT NOT STARTED",
            )

        if (
            not math.isfinite(now_s)
            or not math.isfinite(
                self.last_beat_s
            )
        ):
            return AppHeartbeatState(
                healthy=False,
                stalled=True,
                age_s=0.0,
                message="APP HEARTBEAT INVALID",
            )

        age_s = (
            now_s - self.last_beat_s
        )

        if age_s < 0.0:
            return AppHeartbeatState(
                healthy=False,
                stalled=True,
                age_s=0.0,
                message="APP HEARTBEAT INVALID",
            )

        stalled = (
            age_s > self.stall_after_s
        )

        return AppHeartbeatState(
            healthy=not stalled,
            stalled=stalled,
            age_s=age_s,
            message=(
                "APP LOOP STALLED"
                if stalled
                else "APP LOOP OK"
            ),
        )