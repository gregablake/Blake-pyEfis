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
from pyefis.user.blake_pfd.core.fuel_state_calculator import (
    FuelStateCalculator,
)


class AircraftStateManager:
    def __init__(
        self,
        fuel_calculator: FuelStateCalculator | None = None,
    ) -> None:
        self.state = AircraftState()

        self.fuel_calculator = (
            fuel_calculator
            if fuel_calculator is not None
            else FuelStateCalculator()
        )

    def update(
        self,
        pfd: FlightData,
        engine: EngineData,
        selected_waypoint_id: str,
        flight_state: FlightState | None = None,
        engine_state: EngineState | None = None,
    ) -> AircraftState:
        calculated_fuel = (
            self.fuel_calculator.calculate(
                remaining_gal=engine.fuel_remaining_gal,
                used_gal=engine.fuel_used_gal,
                flow_gph=engine.fuel_flow_gph,
                ground_speed_kt=pfd.ground_speed_kt,
                fallback_endurance_hr=engine.endurance_hr,
                fallback_range_nm=engine.fuel_range_nm,
            )
        )
        self.state = AircraftState(
            flight_state=flight_state,
            engine_state=engine_state,

            # Legacy compatibility for older code
            engine=engine,

            fuel=FuelState(
                remaining_gal=(
                    calculated_fuel.remaining_gal
                ),
                used_gal=(
                    calculated_fuel.used_gal
                ),
                flow_gph=(
                    calculated_fuel.flow_gph
                ),
                endurance_hr=(
                    calculated_fuel.endurance_hr
                ),
                range_nm=(
                    calculated_fuel.range_nm
                ),
                calculation_valid=(
                    calculated_fuel.calculation_valid
                ),
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