from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.core.flight_state_manager import FlightStateManager


def pfd(gs: float, alt: float = 1000.0, vsi: float = 0.0):
    return SimpleNamespace(
        ground_speed_kt=gs,
        pressure_alt_ft=alt,
        vsi_fpm=vsi,
    )


def engine(rpm: float):
    return SimpleNamespace(rpm=rpm)


def test_parked_phase() -> None:
    manager = FlightStateManager()

    state = manager.update(
        pfd(0.0),
        engine=engine(800.0),
    )

    assert state.phase == "PARKED"
    assert state.aircraft_moving is False
    assert state.airborne is False


def test_runup_phase() -> None:
    manager = FlightStateManager()

    state = manager.update(
        pfd(0.0),
        engine=engine(1700.0),
    )

    assert state.phase == "RUNUP"


def test_taxi_phase() -> None:
    manager = FlightStateManager()

    state = manager.update(
        pfd(12.0),
        engine=engine(1000.0),
    )

    assert state.phase == "TAXI"
    assert state.aircraft_moving is True


def test_takeoff_phase() -> None:
    manager = FlightStateManager()

    state = manager.update(
        pfd(40.0),
        engine=engine(2450.0),
    )

    assert state.phase == "TAKEOFF"
    assert state.takeoff_roll is True


def test_climb_phase() -> None:
    manager = FlightStateManager()

    state = manager.update(
        pfd(75.0, alt=1600.0, vsi=800.0),
        engine=engine(2450.0),
    )

    assert state.phase == "CLIMB"
    assert state.airborne is True


def test_cruise_phase() -> None:
    manager = FlightStateManager()

    state = manager.update(
        pfd(95.0, alt=3500.0, vsi=0.0),
        engine=engine(2350.0),
    )

    assert state.phase == "CRUISE"


def test_descent_phase() -> None:
    manager = FlightStateManager()

    state = manager.update(
        pfd(90.0, alt=3000.0, vsi=-600.0),
        engine=engine(2200.0),
    )

    assert state.phase == "DESCENT"