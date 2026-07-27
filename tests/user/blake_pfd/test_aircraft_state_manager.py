from types import SimpleNamespace

import pytest

from pyefis.user.blake_pfd.core.aircraft_state_manager import (
    AircraftStateManager,
)
from pyefis.user.blake_pfd.engine_data import EngineData

def test_aircraft_state_manager_builds_complete_state() -> None:
    manager = AircraftStateManager()

    pfd = SimpleNamespace(
        bearing_deg=90.0,
        distance_to_waypoint_nm=12.5,
        desired_track_deg=92.0,
        course_error_deg=-2.0,
        ground_speed_kt=105.0,
        pressure_alt_ft=3500.0,
        vsi_fpm=250.0,
    )

    engine = SimpleNamespace(
        fuel_remaining_gal=18.0,
        fuel_used_gal=6.0,
        fuel_flow_gph=8.5,
        endurance_hr=2.1,
        fuel_range_nm=220.0,
        volts=14.2,
        amps=8.0,
        alternator_online=True,
    )

    flight_state = SimpleNamespace(
        phase="CRUISE",
        aircraft_moving=True,
        airborne=True,
    )

    engine_state = SimpleNamespace()

    result = manager.update(
        pfd=pfd,
        engine=engine,
        selected_waypoint_id="KHAO",
        flight_state=flight_state,
        engine_state=engine_state,
    )

    assert result.flight_state is flight_state
    assert result.engine_state is engine_state
    assert result.engine is engine

    assert result.fuel.remaining_gal == 18.0
    assert result.fuel.used_gal == 6.0
    assert result.fuel.flow_gph == 8.5
    assert result.fuel.endurance_hr == pytest.approx(18.0 / 8.5)

    assert result.fuel.range_nm == pytest.approx(
    (18.0 / 8.5) * 105.0
    )

    assert result.electrical.volts == 14.2
    assert result.electrical.amps == 8.0
    assert result.electrical.alternator_online is True

    assert result.navigation.selected_waypoint_id == "KHAO"
    assert result.navigation.bearing_deg == 90.0
    assert result.navigation.distance_nm == 12.5
    assert result.navigation.desired_track_deg == 92.0
    assert result.navigation.course_error_deg == -2.0

    assert result.ground_speed_kt == 105.0
    assert result.altitude_ft == 3500.0
    assert result.vsi_fpm == 250.0
    
def test_aircraft_state_manager_accepts_real_engine_data() -> None:
    manager = AircraftStateManager()

    pfd = SimpleNamespace(
        bearing_deg=180.0,
        distance_to_waypoint_nm=50.0,
        desired_track_deg=182.0,
        course_error_deg=-2.0,
        ground_speed_kt=110.0,
        pressure_alt_ft=4500.0,
        vsi_fpm=0.0,
    )

    engine = EngineData(
        fuel_remaining_gal=16.0,
        fuel_used_gal=8.0,
        fuel_flow_gph=8.0,
        endurance_hr=2.0,
        fuel_range_nm=220.0,
        volts=14.1,
        amps=7.0,
        alternator_online=True,
    )

    result = manager.update(
        pfd=pfd,
        engine=engine,
        selected_waypoint_id="KDAY",
    )

    assert result.engine is engine
    assert result.fuel.remaining_gal == 16.0
    assert result.fuel.flow_gph == 8.0
    assert result.fuel.endurance_hr == 2.0
    assert result.fuel.range_nm == 220.0
    assert result.navigation.distance_nm == 50.0
    assert result.ground_speed_kt == 110.0
    assert result.fuel.calculation_valid is True
def test_engine_data_has_default_fuel_range() -> None:
    engine = EngineData()

    assert engine.fuel_range_nm == 0.0
    
def test_aircraft_state_manager_calculates_live_fuel_range() -> None:
    manager = AircraftStateManager()

    pfd = SimpleNamespace(
        bearing_deg=0.0,
        distance_to_waypoint_nm=0.0,
        desired_track_deg=0.0,
        course_error_deg=0.0,
        ground_speed_kt=120.0,
        pressure_alt_ft=3000.0,
        vsi_fpm=0.0,
    )

    engine = EngineData(
        fuel_remaining_gal=12.0,
        fuel_used_gal=4.0,
        fuel_flow_gph=8.0,
        endurance_hr=99.0,
        fuel_range_nm=999.0,
    )

    result = manager.update(
        pfd=pfd,
        engine=engine,
        selected_waypoint_id="",
    )

    assert result.fuel.endurance_hr == 1.5
    assert result.fuel.range_nm == 180.0
    assert result.fuel.calculation_valid is True
    
def test_aircraft_state_manager_calculates_wind_components() -> None:
    manager = AircraftStateManager()

    pfd = SimpleNamespace(
        bearing_deg=90.0,
        distance_to_waypoint_nm=25.0,
        desired_track_deg=0.0,
        course_error_deg=0.0,
        ground_speed_kt=100.0,
        pressure_alt_ft=3000.0,
        vsi_fpm=0.0,
    )

    engine = EngineData(
        fuel_remaining_gal=10.0,
        fuel_used_gal=5.0,
        fuel_flow_gph=8.0,
    )

    result = manager.update(
        pfd=pfd,
        engine=engine,
        selected_waypoint_id="KHAO",
        wind_speed_kt=20.0,
        wind_from_deg=45.0,
    )

    assert result.wind.valid is True

    assert result.wind.headwind_kt == pytest.approx(
        14.142,
        rel=1e-3,
    )

    assert result.wind.crosswind_kt == pytest.approx(
        14.142,
        rel=1e-3,
    )

    assert result.wind.crosswind_direction == "RIGHT"
    
def test_aircraft_state_manager_handles_invalid_wind() -> None:
    manager = AircraftStateManager()

    pfd = SimpleNamespace(
        bearing_deg=0.0,
        distance_to_waypoint_nm=0.0,
        desired_track_deg=0.0,
        course_error_deg=0.0,
        ground_speed_kt=100.0,
        pressure_alt_ft=3000.0,
        vsi_fpm=0.0,
    )

    engine = EngineData()

    result = manager.update(
        pfd=pfd,
        engine=engine,
        selected_waypoint_id="",
        wind_speed_kt=float("nan"),
        wind_from_deg=90.0,
    )

    assert result.wind.valid is False
    assert result.wind.headwind_kt == 0.0
    assert result.wind.crosswind_kt == 0.0