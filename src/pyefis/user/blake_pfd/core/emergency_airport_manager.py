from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.emergency_airport_advisor import (
    EmergencyAirportAdvice,
    EmergencyAirportAdvisor,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    NearbyAirportRecord,
    ReachableAirportPipeline,
    ReachableAirportResult,
)


@dataclass(frozen=True)
class EmergencyAirportState:
    result: ReachableAirportResult = ReachableAirportResult()
    advice: EmergencyAirportAdvice = EmergencyAirportAdvice()


class EmergencyAirportManager:
    def __init__(
        self,
        pipeline: ReachableAirportPipeline | None = None,
        advisor: EmergencyAirportAdvisor | None = None,
    ) -> None:
        self.pipeline = (
            pipeline
            if pipeline is not None
            else ReachableAirportPipeline()
        )

        self.advisor = (
            advisor
            if advisor is not None
            else EmergencyAirportAdvisor()
        )

        self.state = EmergencyAirportState()

    def update(
        self,
        airports: list[NearbyAirportRecord],
        aircraft_altitude_ft,
        terrain_elevation_ft=0.0,
        wind_speed_kt=0.0,
        wind_from_deg=0.0,
        emergency_active: bool = False,
    ) -> EmergencyAirportState:
        result = self.pipeline.evaluate(
            airports=airports,
            aircraft_altitude_ft=aircraft_altitude_ft,
            terrain_elevation_ft=terrain_elevation_ft,
            wind_speed_kt=wind_speed_kt,
            wind_from_deg=wind_from_deg,
        )

        advice = self.advisor.advise(
            result=result,
            emergency_active=emergency_active,
        )

        self.state = EmergencyAirportState(
            result=result,
            advice=advice,
        )

        return self.state

    def clear(self) -> None:
        self.state = EmergencyAirportState()