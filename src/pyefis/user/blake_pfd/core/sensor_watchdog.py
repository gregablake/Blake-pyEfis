from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorWatchdogState:
    flight_data_available: bool
    position_valid: bool
    attitude_valid: bool
    air_data_valid: bool
    degraded: bool
    failed: bool
    message: str


class SensorWatchdog:
    def evaluate(
        self,
        *,
        flight_data_available: bool,
        position_valid: bool,
        attitude_valid: bool = True,
        air_data_valid: bool = True,
    ) -> SensorWatchdogState:
        if not flight_data_available:
            return SensorWatchdogState(
                flight_data_available=False,
                position_valid=False,
                attitude_valid=False,
                air_data_valid=False,
                degraded=False,
                failed=True,
                message="FLIGHT DATA LOST",
            )

        failures: list[str] = []

        if not attitude_valid:
            failures.append("ATTITUDE")

        if not air_data_valid:
            failures.append("AIR DATA")

        if not position_valid:
            failures.append("GPS")

        if failures:
            return SensorWatchdogState(
                flight_data_available=True,
                position_valid=position_valid,
                attitude_valid=attitude_valid,
                air_data_valid=air_data_valid,
                degraded=True,
                failed=False,
                message=(
                    "DEGRADED: "
                    + " / ".join(failures)
                ),
            )

        return SensorWatchdogState(
            flight_data_available=True,
            position_valid=True,
            attitude_valid=True,
            air_data_valid=True,
            degraded=False,
            failed=False,
            message="SENSORS OK",
        )