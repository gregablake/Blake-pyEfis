from __future__ import annotations

import pytest

from pyefis.user.blake_pfd.core.sensor_manager import (
    EngineDataUnavailableError,
    SensorManager,
    SensorMode,
    UnavailableEngineSource,
)
from pyefis.user.blake_pfd.engine_sim import SimulatedEngineSource
from pyefis.user.blake_pfd.flight_computer import FlightComputer


def test_simulation_mode_uses_simulated_engine_source() -> None:
    manager = SensorManager(
        flight_computer=FlightComputer(),
        use_hardware=False,
    )

    assert manager.mode is SensorMode.SIMULATION
    assert isinstance(
        manager.engine_source,
        SimulatedEngineSource,
    )


def test_hardware_mode_uses_unavailable_engine_source() -> None:
    manager = SensorManager(
        flight_computer=FlightComputer(),
        use_hardware=True,
    )

    assert manager.mode is SensorMode.HARDWARE
    assert isinstance(
        manager.engine_source,
        UnavailableEngineSource,
    )
    assert not isinstance(
        manager.engine_source,
        SimulatedEngineSource,
    )


def test_hardware_engine_read_fails_closed() -> None:
    manager = SensorManager(
        flight_computer=FlightComputer(),
        use_hardware=True,
    )

    with pytest.raises(
        EngineDataUnavailableError,
        match="Real engine sensor source is not configured",
    ):
        manager.read_engine()
