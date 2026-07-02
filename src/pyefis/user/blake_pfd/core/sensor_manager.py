from __future__ import annotations

from enum import Enum

from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.engine_sim import SimulatedEngineSource
from pyefis.user.blake_pfd.flight_computer import FlightComputer, FlightData
from pyefis.user.blake_pfd.hardware_readers import BlakeHardwareSensorSource
from pyefis.user.blake_pfd.log_replay import LogReplaySource
from pyefis.user.blake_pfd.sensors_sim import SimulatedSensorSource


class SensorMode(str, Enum):
    SIMULATION = "simulation"
    HARDWARE = "hardware"
    REPLAY = "replay"


class SensorManager:
    def __init__(
        self,
        flight_computer: FlightComputer,
        use_hardware: bool = False,
        replay_log: str | None = None,
    ) -> None:
        self.flight_computer = flight_computer
        self.replay_source = LogReplaySource(replay_log) if replay_log else None
        self.flight_sensor_source = (
            BlakeHardwareSensorSource()
            if use_hardware
            else SimulatedSensorSource()
        )
        self.engine_source = SimulatedEngineSource()

        if replay_log:
            self.mode = SensorMode.REPLAY
        elif use_hardware:
            self.mode = SensorMode.HARDWARE
        else:
            self.mode = SensorMode.SIMULATION

    def read_flight(self) -> FlightData:
        if self.replay_source is not None:
            return self.replay_source.read()

        raw = self.flight_sensor_source.read()
        return self.flight_computer.update(raw)

    def read_engine(self) -> EngineData:
        return self.engine_source.read()