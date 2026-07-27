from __future__ import annotations

from dataclasses import dataclass, field

from pyefis.user.blake_pfd.core.flight_state_manager import FlightState
from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.core.engine_state import EngineState
from pyefis.user.blake_pfd.core.emergency_airport_manager import (
    EmergencyAirportState,
)


@dataclass
class NavigationState:
    selected_waypoint_id: str = ""
    bearing_deg: float = 0.0
    distance_nm: float = 0.0
    desired_track_deg: float = 0.0
    course_error_deg: float = 0.0


@dataclass
class FuelState:
    remaining_gal: float = 0.0
    used_gal: float = 0.0
    flow_gph: float = 0.0
    endurance_hr: float = 0.0
    range_nm: float = 0.0
    calculation_valid: bool = False


@dataclass
class ElectricalState:
    volts: float = 0.0
    amps: float = 0.0
    alternator_online: bool = True
    
@dataclass
class WindState:
    speed_kt: float = 0.0
    from_deg: float = 0.0
    headwind_kt: float = 0.0
    tailwind_kt: float = 0.0
    crosswind_kt: float = 0.0
    crosswind_direction: str = "NONE"
    valid: bool = False


@dataclass
class AircraftState:
    # Major state objects
    flight_state: FlightState | None = None
    engine_state: EngineState | None = None

    fuel: FuelState = field(default_factory=FuelState)
    electrical: ElectricalState = field(default_factory=ElectricalState)
    navigation: NavigationState = field(default_factory=NavigationState)
    wind: WindState = field(default_factory=WindState)
    emergency_airport: EmergencyAirportState = field(
        default_factory=EmergencyAirportState
    )

    # Legacy compatibility (remove after migration)
    engine: EngineData | None = None

    # Frequently used values
    ground_speed_kt: float = 0.0
    altitude_ft: float = 0.0
    vsi_fpm: float = 0.0