from __future__ import annotations

from pyefis.user.blake_pfd.core.aircraft_state import (
    AircraftState,
    ElectricalState,
    FuelState,
    NavigationState,
)
from pyefis.user.blake_pfd.core.engine_state import EngineState
from pyefis.user.blake_pfd.core.flight_state_manager import FlightState
from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.flight_computer import FlightData


class AircraftStateManager:
    def __init__(self) -> None:
        self.state = AircraftState()

    def update(
        self,
        pfd: FlightData,
        engine: EngineData,
        selected_waypoint_id: str,
        flight_state: FlightState | None = None,
        engine_state: EngineState | None = None,
    ) -> AircraftState:
        self.state = AircraftState(
            flight_state=flight_state,
            engine_state=engine_state,

            # Legacy compatibility for older code
            engine=engine,

            fuel=FuelState(
                remaining_gal=engine.fuel_remaining_gal,
                used_gal=engine.fuel_used_gal,
                flow_gph=engine.fuel_flow_gph,
                endurance_hr=engine.endurance_hr,
                range_nm=engine.fuel_range_nm,
            ),
            electrical=ElectricalState(
                volts=engine.volts,
                amps=engine.amps,
                alternator_online=engine.alternator_online,
            ),
            navigation=NavigationState(
                selected_waypoint_id=selected_waypoint_id,
                bearing_deg=pfd.bearing_deg,
                distance_nm=pfd.distance_to_waypoint_nm,
                desired_track_deg=pfd.desired_track_deg,
                course_error_deg=pfd.course_error_deg,
            ),
            ground_speed_kt=pfd.ground_speed_kt,
            altitude_ft=pfd.pressure_alt_ft,
            vsi_fpm=pfd.vsi_fpm,
        )

        return self.state