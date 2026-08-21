from __future__ import annotations

from pyefis.user.blake_pfd.core.aircraft_state import (
    AircraftState,
    ElectricalState,
    FuelState,
    NavigationState,
    WindState,
)
from pyefis.user.blake_pfd.core.engine_state import EngineState
from pyefis.user.blake_pfd.core.flight_state_manager import FlightState
from pyefis.user.blake_pfd.core.fuel_state_calculator import (
    FuelStateCalculator,
)
from pyefis.user.blake_pfd.core.wind_calculator import (
    WindCalculator,
)
from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.flight_computer import FlightData

from pyefis.user.blake_pfd.core.emergency_airport_manager import (
    EmergencyAirportState,
)


class AircraftStateManager:
    def __init__(
        self,
        fuel_calculator: FuelStateCalculator | None = None,
        wind_calculator: WindCalculator | None = None,
    ) -> None:
        self.state = AircraftState()

        self.fuel_calculator = (
            fuel_calculator
            if fuel_calculator is not None
            else FuelStateCalculator()
        )

        self.wind_calculator = (
            wind_calculator
            if wind_calculator is not None
            else WindCalculator()
        )

    def update(
        self,
        pfd: FlightData,
        engine: EngineData | None,
        selected_waypoint_id: str,
        flight_state: FlightState | None = None,
        engine_state: EngineState | None = None,
        wind_speed_kt: float = 0.0,
        wind_from_deg: float = 0.0,
        emergency_airport_state: EmergencyAirportState | None = None,
    ) -> AircraftState:
        if engine is None:
            fuel_state = FuelState(
                calculation_valid=False,
            )

            electrical_state = ElectricalState(
                volts=0.0,
                amps=0.0,
                alternator_online=False,
                valid=False,
            )

        else:
            calculated_fuel = (
                self.fuel_calculator.calculate(
                    remaining_gal=(
                        engine.fuel_remaining_gal
                    ),
                    used_gal=engine.fuel_used_gal,
                    flow_gph=engine.fuel_flow_gph,
                    ground_speed_kt=(
                        pfd.ground_speed_kt
                    ),
                    fallback_endurance_hr=(
                        engine.endurance_hr
                    ),
                    fallback_range_nm=(
                        engine.fuel_range_nm
                    ),
                )
            )

            fuel_state = FuelState(
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
            )

            electrical_state = ElectricalState(
                volts=engine.volts,
                amps=engine.amps,
                alternator_online=(
                    engine.alternator_online
                ),
                valid=True,
            )

        calculated_wind = (
            self.wind_calculator.calculate_components(
                wind_speed_kt=wind_speed_kt,
                wind_from_deg=wind_from_deg,
                course_deg=pfd.desired_track_deg,
            )
        )

        self.state = AircraftState(
            flight_state=flight_state,
            engine_state=engine_state,

            engine=engine,

            fuel=fuel_state,

            electrical=electrical_state,

            navigation=NavigationState(
                selected_waypoint_id=selected_waypoint_id,
                bearing_deg=pfd.bearing_deg,
                distance_nm=pfd.distance_to_waypoint_nm,
                desired_track_deg=pfd.desired_track_deg,
                course_error_deg=pfd.course_error_deg,
            ),

            wind=WindState(
                speed_kt=calculated_wind.wind_speed_kt,
                from_deg=calculated_wind.wind_from_deg,
                headwind_kt=calculated_wind.headwind_kt,
                tailwind_kt=calculated_wind.tailwind_kt,
                crosswind_kt=calculated_wind.crosswind_kt,
                crosswind_direction=(
                    calculated_wind.crosswind_direction
                ),
                valid=calculated_wind.valid,
            ),

            emergency_airport=(
                emergency_airport_state
                if emergency_airport_state is not None
                else EmergencyAirportState()
            ),

            ground_speed_kt=pfd.ground_speed_kt,
            altitude_ft=pfd.pressure_alt_ft,
            vsi_fpm=pfd.vsi_fpm,
        )

        return self.state