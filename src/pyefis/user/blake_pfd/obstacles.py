from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Obstacle:
    ident: str
    lat_deg: float
    lon_deg: float
    elevation_ft: float
    height_agl_ft: float
    distance_nm: float = 0.0
    bearing_deg: float = 0.0


@dataclass
class ObstacleState:
    ok: bool = True
    nearby: list[Obstacle] | None = None
    warning: bool = False


class ObstacleComputer:
    def update(self, aircraft_lat: float, aircraft_lon: float, aircraft_alt_ft: float) -> ObstacleState:
        # Placeholder obstacle near Cincinnati.
        obstacle = Obstacle(
            ident="TEST TOWER",
            lat_deg=39.11,
            lon_deg=-84.51,
            elevation_ft=1200.0,
            height_agl_ft=500.0,
            distance_nm=1.2,
            bearing_deg=15.0,
        )

        vertical_clearance = aircraft_alt_ft - obstacle.elevation_ft
        warning = obstacle.distance_nm < 3.0 and vertical_clearance < 1000.0

        return ObstacleState(
            ok=True,
            nearby=[obstacle],
            warning=warning,
        )