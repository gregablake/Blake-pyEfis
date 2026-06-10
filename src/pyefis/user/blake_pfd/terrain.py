from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TerrainState:
    ok: bool = False
    terrain_elevation_ft: float = 0.0
    clearance_ft: float = 9999.0
    warning_level: str = "none"


class TerrainComputer:
    def __init__(self) -> None:
        pass

    def update(self, aircraft_alt_ft: float, aircraft_lat: float, aircraft_lon: float) -> TerrainState:
        # Placeholder terrain elevation until real terrain DB is added.
        terrain_elevation_ft = 700.0
        clearance_ft = aircraft_alt_ft - terrain_elevation_ft

        if clearance_ft < 300:
            warning = "red"
        elif clearance_ft < 700:
            warning = "yellow"
        else:
            warning = "none"

        return TerrainState(
            ok=True,
            terrain_elevation_ft=terrain_elevation_ft,
            clearance_ft=clearance_ft,
            warning_level=warning,
        )