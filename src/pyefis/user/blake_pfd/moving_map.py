from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MapAirport:
    ident: str
    name: str
    distance_nm: float
    bearing_deg: float
    x: int = 0
    y: int = 0


@dataclass
class MovingMapState:
    airports: list[MapAirport]
    range_nm: float = 25.0


class MovingMapComputer:
    def update(self, database, aircraft_lat: float, aircraft_lon: float) -> MovingMapState:
        nearest = database.nearest_airports(
            aircraft_lat,
            aircraft_lon,
            max_results=8,
        )

        airports = [
            MapAirport(
                ident=airport.ident,
                name=airport.name,
                distance_nm=distance_nm,
                bearing_deg=0.0,
            )
            for distance_nm, airport in nearest
        ]

        return MovingMapState(airports=airports)