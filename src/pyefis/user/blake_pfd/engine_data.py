from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EngineData:
    rpm: float = 0.0

    volts: float = 0.0
    amps: float = 0.0

    oil_pressure_psi: float = 0.0
    oil_temp_f: float = 0.0
    fuel_pressure_psi: float = 0.0

    cht_f: list[float] = field(default_factory=lambda: [0.0] * 6)
    egt_f: list[float] = field(default_factory=lambda: [0.0] * 2)

    ignition_a: bool = False
    ignition_b: bool = False
    alternator_online: bool = False
    starter_engaged: bool = False
    fuel_flow_gph: float = 0.0
    fuel_remaining_gal: float = 0.0
    fuel_used_gal: float = 0.0
    endurance_hr: float = 0.0