from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RebootRecoveryState:
    previous_shutdown_clean: bool
    recovery_required: bool
    inhibit_ready: bool
    message: str


class RebootRecovery:
    def evaluate(
        self,
        *,
        previous_shutdown_clean: bool,
        startup_ready: bool,
        flight_data_valid: bool,
    ) -> RebootRecoveryState:
        if not previous_shutdown_clean:
            if not flight_data_valid:
                return RebootRecoveryState(
                    previous_shutdown_clean=False,
                    recovery_required=True,
                    inhibit_ready=True,
                    message=(
                        "UNCLEAN RESTART - "
                        "WAITING FOR FLIGHT DATA"
                    ),
                )

            if not startup_ready:
                return RebootRecoveryState(
                    previous_shutdown_clean=False,
                    recovery_required=True,
                    inhibit_ready=True,
                    message=(
                        "UNCLEAN RESTART - "
                        "SYSTEM RECHECK"
                    ),
                )

            return RebootRecoveryState(
                previous_shutdown_clean=False,
                recovery_required=True,
                inhibit_ready=False,
                message="RECOVERED AFTER UNCLEAN RESTART",
            )

        if not startup_ready:
            return RebootRecoveryState(
                previous_shutdown_clean=True,
                recovery_required=False,
                inhibit_ready=True,
                message="STARTUP CHECK IN PROGRESS",
            )

        return RebootRecoveryState(
            previous_shutdown_clean=True,
            recovery_required=False,
            inhibit_ready=False,
            message="NORMAL STARTUP",
        )