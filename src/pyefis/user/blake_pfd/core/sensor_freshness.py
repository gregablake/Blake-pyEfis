from __future__ import annotations

from dataclasses import dataclass


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
        attitude_fresh = (
            now - last_attitude_update
            <= attitude_timeout
        )

        air_data_fresh = (
            now - last_air_data_update
            <= air_data_timeout
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