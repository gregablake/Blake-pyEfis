from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.core.aircraft_state_manager import (
    AircraftStateManager,
)
from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)


def test_invalid_electrical_channel_marks_electrical_state_invalid() -> None:
    manager = AircraftStateManager()

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    invalid = EngineChannelStatus(
        valid=False,
        fresh=False,
        message="IMPLAUSIBLE DATA",
    )

    pfd = SimpleNamespace(
        ground_speed_kt=100.0,
        pressure_alt_ft=3000.0,
        vsi_fpm=0.0,
        bearing_deg=0.0,
        distance_to_waypoint_nm=10.0,
        desired_track_deg=0.0,
        course_error_deg=0.0,
    )

    engine = SimpleNamespace(
        fuel_remaining_gal=20.0,
        fuel_used_gal=5.0,
        fuel_flow_gph=8.0,
        endurance_hr=2.5,
        fuel_range_nm=250.0,
        volts=99.0,
        amps=5.0,
        alternator_online=True,
    )

    status = EngineSensorStatus(
        volts=invalid,
        amps=healthy,
    )

    state = manager.update(
        pfd=pfd,
        engine=engine,
        selected_waypoint_id="",
        sensor_status=status,
    )

    assert state.electrical.valid is False
    
def test_invalid_fuel_flow_marks_fuel_calculation_invalid() -> None:
    manager = AircraftStateManager()

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    invalid = EngineChannelStatus(
        valid=False,
        fresh=False,
        message="IMPLAUSIBLE DATA",
    )

    pfd = SimpleNamespace(
        ground_speed_kt=100.0,
        pressure_alt_ft=3000.0,
        vsi_fpm=0.0,
        bearing_deg=0.0,
        distance_to_waypoint_nm=10.0,
        desired_track_deg=0.0,
        course_error_deg=0.0,
    )

    engine = SimpleNamespace(
        fuel_remaining_gal=20.0,
        fuel_used_gal=5.0,
        fuel_flow_gph=99.0,
        endurance_hr=2.5,
        fuel_range_nm=250.0,
        volts=14.2,
        amps=5.0,
        alternator_online=True,
    )

    status = EngineSensorStatus(
        volts=healthy,
        amps=healthy,
        fuel_flow=invalid,
    )

    state = manager.update(
        pfd=pfd,
        engine=engine,
        selected_waypoint_id="",
        sensor_status=status,
    )

    assert state.fuel.calculation_valid is False