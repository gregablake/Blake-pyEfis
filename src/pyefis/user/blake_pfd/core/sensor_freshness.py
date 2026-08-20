from __future__ import annotations

from dataclasses import dataclass

import math
@dataclass(frozen=True)
class SensorFreshnessState:
    attitude_fresh: bool
    air_data_fresh: bool
    flight_data_fresh: bool
    message: str


class SensorFreshness:
    def evaluate(
        self,
        *,
        now: float,
        last_attitude_update: float,
        last_air_data_update: float,
        attitude_timeout: float,
        air_data_timeout: float,
    ) -> SensorFreshnessState:
        
        values = (
            now,
            last_attitude_update,
            last_air_data_update,
            attitude_timeout,
            air_data_timeout,
        )

        if not all(
            math.isfinite(value)
            for value in values
        ):
            return SensorFreshnessState(
                attitude_fresh=False,
                air_data_fresh=False,
                flight_data_fresh=False,
                message="STALE: ATTITUDE / AIR DATA",
            )

        if (
            attitude_timeout < 0.0
            or air_data_timeout < 0.0
        ):
            return SensorFreshnessState(
                attitude_fresh=False,
                air_data_fresh=False,
                flight_data_fresh=False,
                message="STALE: ATTITUDE / AIR DATA",
            )
        attitude_age = (
            now - last_attitude_update
        )

        air_data_age = (
            now - last_air_data_update
        )

        attitude_fresh = (
            0.0 <= attitude_age <= attitude_timeout
        )

        air_data_fresh = (
            0.0 <= air_data_age <= air_data_timeout
        )

        failures: list[str] = []

        if not attitude_fresh:
            failures.append("ATTITUDE")

        if not air_data_fresh:
            failures.append("AIR DATA")

        if failures:
            return SensorFreshnessState(
                attitude_fresh=attitude_fresh,
                air_data_fresh=air_data_fresh,
                flight_data_fresh=False,
                message=(
                    "STALE: "
                    + " / ".join(failures)
                ),
            )

        return SensorFreshnessState(
            attitude_fresh=True,
            air_data_fresh=True,
            flight_data_fresh=True,
            message="FLIGHT DATA FRESH",
        )