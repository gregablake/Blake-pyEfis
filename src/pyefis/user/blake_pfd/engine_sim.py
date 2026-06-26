from __future__ import annotations

from math import sin
from time import monotonic

from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.engine_data import EngineData


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
        fuel_used_gal = max(0.0, self.total_fuel_gal - fuel_remaining_gal)
        endurance_hr = fuel_remaining_gal / fuel_flow_gph if fuel_flow_gph > 0 else 0.0

        volts = 13.9
        amps = 8.0 + sin(elapsed_s * 0.2) * 2.0

        cht_base = 325.0 + sin(elapsed_s * 0.2) * 10.0
        egt_base = 1325.0 + sin(elapsed_s * 0.25) * 25.0

        engine = EngineData(
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
            ignition_b=True,
            alternator_online=True,
            starter_engaged=False,
        )

        self.apply_test_mode(engine)

        return engine

    def apply_test_mode(self, engine: EngineData) -> None:
        mode = getattr(self.config.ems_test, "mode", "normal")

        if mode == "normal":
            return

        if mode == "high_cht":
            engine.cht_f[2] = 455.0
            return

        if mode == "high_egt":
            engine.egt_f[0] = 1610.0
            return

        if mode == "low_oil":
            engine.rpm = 2450.0
            engine.oil_pressure_psi = 12.0
            return

        if mode == "alt_fail":
            engine.alternator_online = False
            engine.volts = 12.2
            engine.amps = -4.0
            return

        if mode == "ign_fail":
            engine.ignition_b = False
            return

        if mode == "low_fuel":
            engine.fuel_remaining_gal = 2.5
            engine.fuel_used_gal = max(
                0.0,
                self.config.fuel.total_gal - engine.fuel_remaining_gal,
            )
            engine.endurance_hr = (
                engine.fuel_remaining_gal / engine.fuel_flow_gph
                if engine.fuel_flow_gph > 0
                else 0.0
            )
            return


def demo() -> None:
    source = SimulatedEngineSource()
    print(source.read())


if __name__ == "__main__":
    demo()