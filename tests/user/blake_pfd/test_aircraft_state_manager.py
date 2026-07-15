from types import SimpleNamespace

from pyefis.user.blake_pfd.core.aircraft_state_manager import (
    AircraftStateManager,
)


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
    assert result.fuel.endurance_hr == 2.1
    assert result.fuel.range_nm == 220.0

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