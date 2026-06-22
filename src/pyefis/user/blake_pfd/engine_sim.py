from __future__ import annotations

from math import sin
from time import monotonic

from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.config_loader import load_config


class SimulatedEngineSource:
    def __init__(self) -> None:
        self.start_time_s = monotonic()
        self.config = load_config()
        self.total_fuel_gal = self.config.fuel.remaining_gal

    def read(self) -> EngineData:
        elapsed_s = monotonic() - self.start_time_s

        self.config = load_config()
        self.total_fuel_gal = self.config.fuel.remaining_gal

        rpm = 2450.0 + sin(elapsed_s * 0.4) * 120.0

        oil_temp_f = min(195.0, 75.0 + elapsed_s * 2.0)
        oil_pressure_psi = 45.0 + sin(elapsed_s * 0.3) * 3.0

        fuel_pressure_psi = 4.8 + sin(elapsed_s * 0.5) * 0.2
        fuel_flow_gph = 6.5 + sin(elapsed_s * 0.25) * 0.4
        fuel_remaining_gal = max(
            0.0,
            self.total_fuel_gal - ((fuel_flow_gph * elapsed_s) / 3600.0),
        )
        fuel_used_gal = self.total_fuel_gal - fuel_remaining_gal
        endurance_hr = fuel_remaining_gal / fuel_flow_gph if fuel_flow_gph > 0 else 0.0

        volts = 13.9
        amps = 8.0 + sin(elapsed_s * 0.2) * 2.0

        cht_base = 325.0 + sin(elapsed_s * 0.2) * 10.0
        egt_base = 1325.0 + sin(elapsed_s * 0.25) * 25.0

        return EngineData(
            rpm=rpm,
            volts=volts,
            amps=amps,
            oil_pressure_psi=oil_pressure_psi,
            oil_temp_f=oil_temp_f,
            fuel_pressure_psi=fuel_pressure_psi,
            fuel_flow_gph=fuel_flow_gph,
            fuel_remaining_gal=fuel_remaining_gal,
            fuel_used_gal=fuel_used_gal,
            endurance_hr=endurance_hr,
            cht_f=[
                cht_base + 0,
                cht_base - 7,
                cht_base + 5,
                cht_base - 3,
                cht_base - 6,
                cht_base + 2,
            ],
            egt_f=[
                egt_base,
                egt_base - 12,
            ],
            ignition_a=True,
            ignition_b=(elapsed_s % 180 < 170),
            alternator_online=(elapsed_s % 120 < 110),
            starter_engaged=False,
        )


def demo() -> None:
    source = SimulatedEngineSource()
    print(source.read())


if __name__ == "__main__":
    demo()