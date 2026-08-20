from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorWatchdogState:
    flight_data_available: bool
    position_valid: bool
    position_fresh: bool
    attitude_valid: bool
    air_data_valid: bool
    attitude_fresh: bool
    air_data_fresh: bool
    degraded: bool
    failed: bool
    message: str


class SensorWatchdog:
    def evaluate(
        self,
        *,
        flight_data_available: bool,
        position_valid: bool,
        position_fresh: bool = True,
        attitude_valid: bool = True,
        air_data_valid: bool = True,
        attitude_fresh: bool = True,
        air_data_fresh: bool = True,
    ) -> SensorWatchdogState:
        if not flight_data_available:
            return SensorWatchdogState(
                flight_data_available=False,
                position_valid=False,
                position_fresh=False,
                attitude_valid=False,
                air_data_valid=False,
                attitude_fresh=False,
                air_data_fresh=False,
                degraded=False,
                failed=True,
                message="FLIGHT DATA LOST",
            )

        failures: list[str] = []

        if not attitude_valid:
            failures.append("ATTITUDE")
        elif not attitude_fresh:
            failures.append("ATTITUDE STALE")

        if not air_data_valid:
            failures.append("AIR DATA")
        elif not air_data_fresh:
            failures.append("AIR DATA STALE")

        if not position_valid:
            failures.append("GPS")
        elif not position_fresh:
            failures.append("GPS STALE")

        if failures:
            return SensorWatchdogState(
                flight_data_available=True,
                position_valid=position_valid,
                position_fresh=position_fresh,
                attitude_valid=attitude_valid,
                air_data_valid=air_data_valid,
                attitude_fresh=attitude_fresh,
                air_data_fresh=air_data_fresh,
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
            position_fresh=True,
            attitude_valid=True,
            air_data_valid=True,
            attitude_fresh=True,
            air_data_fresh=True,
            degraded=False,
            failed=False,
            message="SENSORS OK",
        )
