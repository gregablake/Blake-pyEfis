from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.nav_math import (
    bearing_between_points_deg,
)


@dataclass
class MapAirport:
    ident: str
    name: str
    distance_nm: float
    bearing_deg: float
    relative_x: float = 0.0
    relative_y: float = 0.0


@dataclass
class MovingMapState:
    airports: list[MapAirport]
    range_nm: float = 25.0


class MovingMapComputer:
    def update(self, database, aircraft_lat: float, aircraft_lon: float, range_nm: float = 25.0) -> MovingMapState:
        nearest = database.nearest_airports(
            aircraft_lat,
            aircraft_lon,
            max_results=8,
        )

        airports = []

        for distance_nm, airport in nearest:

            bearing_deg = bearing_between_points_deg(
                aircraft_lat,
                aircraft_lon,
                airport.lat_deg,
                airport.lon_deg,
            )

            airports.append(
                MapAirport(
                    ident=airport.ident,
                    name=airport.name,
                    distance_nm=distance_nm,
                    bearing_deg=bearing_deg,
                )
            )

        return MovingMapState(airports=airports, range_nm=range_nm)