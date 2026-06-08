from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaxiMapState:
    active: bool = False
    airport_id: str = "KHAO"
    airport_name: str = "Butler County Regional"
    ownship_x: int = 0
    ownship_y: int = 0
    heading_deg: float = 0.0


class SafeTaxiComputer:
    def __init__(self, auto_switch_groundspeed_kt: float = 25.0) -> None:
        self.auto_switch_groundspeed_kt = auto_switch_groundspeed_kt

    def update(self, flight) -> TaxiMapState:
        active = flight.ground_speed_kt <= self.auto_switch_groundspeed_kt

        return TaxiMapState(
            active=active,
            heading_deg=flight.heading_deg,
        )