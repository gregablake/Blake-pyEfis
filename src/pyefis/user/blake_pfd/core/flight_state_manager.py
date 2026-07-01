from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FlightState:
    phase: str = "PARKED"
    aircraft_moving: bool = False
    airborne: bool = False
    takeoff_roll: bool = False
    landing_roll: bool = False


class FlightStateManager:
    def __init__(self) -> None:
        self.state = FlightState()

    def update(self, pfd) -> FlightState:
        gs = getattr(pfd, "ground_speed_kt", 0.0)
        alt = getattr(pfd, "pressure_alt_ft", 0.0)
        vsi = getattr(pfd, "vsi_fpm", 0.0)

        aircraft_moving = gs >= 5.0
        takeoff_roll = 30.0 <= gs < 60.0 and vsi >= -100.0
        airborne = gs >= 60.0 or alt > 1500.0
        landing_roll = 10.0 <= gs < 45.0 and vsi <= 100.0

        if gs < 5.0:
            phase = "PARKED"
        elif gs < 30.0:
            phase = "TAXI"
        elif takeoff_roll:
            phase = "TAKEOFF"
        elif airborne and vsi > 300:
            phase = "CLIMB"
        elif airborne and vsi < -300:
            phase = "DESCENT"
        elif airborne:
            phase = "CRUISE"
        elif landing_roll:
            phase = "LANDING"
        else:
            phase = "GROUND"

        self.state = FlightState(
            phase=phase,
            aircraft_moving=aircraft_moving,
            airborne=airborne,
            takeoff_roll=takeoff_roll,
            landing_roll=landing_roll,
        )

        return self.state