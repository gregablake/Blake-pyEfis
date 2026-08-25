from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pyefis.user.blake_pfd.core.event_log import EventLog


class FlightPhase(str, Enum):
    PARKED = "PARKED"
    TAXI = "TAXI"
    RUNUP = "RUNUP"
    TAKEOFF = "TAKEOFF"
    CLIMB = "CLIMB"
    CRUISE = "CRUISE"
    DESCENT = "DESCENT"
    LANDING = "LANDING"


@dataclass
class FlightState:
    phase: str = FlightPhase.PARKED.value
    aircraft_moving: bool = False
    airborne: bool = False
    takeoff_roll: bool = False
    landing_roll: bool = False


class FlightStateManager:
    def __init__(self) -> None:
        self.state = FlightState()
        self.event_log = EventLog()
        self.previous_phase = self.state.phase

    def update(
        self,
        pfd,
        engine=None,
        sensor_status=None,
    ) -> FlightState:
        gs = getattr(pfd, "ground_speed_kt", 0.0)
        alt = getattr(pfd, "pressure_alt_ft", 0.0)
        vsi = getattr(pfd, "vsi_fpm", 0.0)

        rpm_valid = (
            engine is not None
            and (
                sensor_status is None
                or (
                    sensor_status.rpm.valid
                    and sensor_status.rpm.fresh
                )
            )
        )

        rpm = (
            getattr(engine, "rpm", 0.0)
            if rpm_valid
            else None
        )

        aircraft_moving = gs >= 5.0
        airborne = gs >= 55.0 or alt > 1500.0

        takeoff_roll = (
            rpm is not None
            and 30.0 <= gs < 55.0
            and rpm >= 2200.0
        )

        landing_roll = (
            rpm is not None
            and 10.0 <= gs < 45.0
            and rpm < 1800.0
        )

        if (
            rpm is not None
            and gs < 2.0
            and rpm < 1200.0
        ):
            phase = FlightPhase.PARKED.value
        elif (
            rpm is not None
            and gs < 5.0
            and rpm >= 1200.0
        ):
            phase = FlightPhase.RUNUP.value
        elif 5.0 <= gs < 30.0:
            phase = FlightPhase.TAXI.value
        elif takeoff_roll:
            phase = FlightPhase.TAKEOFF.value
        elif airborne and vsi > 300.0:
            phase = FlightPhase.CLIMB.value
        elif airborne and vsi < -300.0:
            phase = FlightPhase.DESCENT.value
        elif landing_roll:
            phase = FlightPhase.LANDING.value
        elif airborne:
            phase = FlightPhase.CRUISE.value
        else:
            phase = FlightPhase.TAXI.value

        self.state = FlightState(
            phase=phase,
            aircraft_moving=aircraft_moving,
            airborne=airborne,
            takeoff_roll=takeoff_roll,
            landing_roll=landing_roll,
        )
        
        if self.state.phase != self.previous_phase:
            self.event_log.write(
                "FLIGHT_PHASE",
                f"{self.previous_phase} -> {self.state.phase}",
            )
            self.previous_phase = self.state.phase

        return self.state