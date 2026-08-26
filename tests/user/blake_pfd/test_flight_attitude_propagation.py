from __future__ import annotations

from pyefis.user.blake_pfd.flight_computer import (
    FlightComputer,
)
from pyefis.user.blake_pfd.sensors_sim import (
    SimulatedSensorSource,
)


def test_flight_computer_propagates_pitch_and_roll() -> None:
    raw = SimulatedSensorSource().read()

    raw.pitch_deg = 7.5
    raw.roll_deg = -18.0

    flight = FlightComputer().update(raw)

    assert flight.pitch_deg == 7.5
    assert flight.roll_deg == -18.0
