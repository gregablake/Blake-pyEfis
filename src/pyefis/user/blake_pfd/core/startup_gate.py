from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StartupGateState:
    ready: bool
    initializing: bool
    blocked: bool
    message: str


class StartupGate:
    def evaluate(
        self,
        *,
        config_ok: bool,
        database_ok: bool,
        flight_data_available: bool,
        attitude_valid: bool,
        air_data_valid: bool,
        hardware_mode: bool,
    ) -> StartupGateState:
        if not config_ok:
            return StartupGateState(
                ready=False,
                initializing=False,
                blocked=True,
                message="STARTUP BLOCKED: CONFIG",
            )

        if not database_ok:
            return StartupGateState(
                ready=False,
                initializing=False,
                blocked=True,
                message="STARTUP BLOCKED: DATABASE",
            )

        if not flight_data_available:
            return StartupGateState(
                ready=False,
                initializing=True,
                blocked=False,
                message="INITIALIZING FLIGHT DATA",
            )

        if hardware_mode:
            missing: list[str] = []

            if not attitude_valid:
                missing.append("AHRS")

            if not air_data_valid:
                missing.append("AIR DATA")

            if missing:
                return StartupGateState(
                    ready=False,
                    initializing=True,
                    blocked=False,
                    message=(
                        "INITIALIZING: "
                        + " / ".join(missing)
                    ),
                )

        return StartupGateState(
            ready=True,
            initializing=False,
            blocked=False,
            message="SYSTEM READY",
        )