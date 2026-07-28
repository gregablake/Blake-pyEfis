from __future__ import annotations

from math import atan2, cos, degrees, isfinite, radians, sin

from pyefis.user.blake_pfd.database_importer import (
    AviationDatabase,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    NearbyAirportRecord,
)


class NearbyAirportProvider:
    def __init__(
        self,
        database: AviationDatabase,
        maximum_results: int = 25,
    ) -> None:
        if maximum_results < 1:
            raise ValueError(
                "maximum_results must be at least 1"
            )

        self.database = database
        self.maximum_results = int(maximum_results)

    def get_nearby_airports(
        self,
        aircraft_lat_deg,
        aircraft_lon_deg,
    ) -> list[NearbyAirportRecord]:
        latitude = self._safe_latitude(
            aircraft_lat_deg
        )

        longitude = self._safe_longitude(
            aircraft_lon_deg
        )

        if latitude is None or longitude is None:
            return []

        nearest = self.database.nearest_airports(
            latitude,
            longitude,
            max_results=self.maximum_results,
        )

        records: list[NearbyAirportRecord] = []

        for distance_nm, airport in nearest:
            bearing_deg = self._initial_bearing_deg(
                latitude,
                longitude,
                airport.lat_deg,
                airport.lon_deg,
            )

            records.append(
                NearbyAirportRecord(
                    identifier=airport.ident,
                    distance_nm=max(
                        0.0,
                        float(distance_nm),
                    ),
                    bearing_deg=bearing_deg,
                    elevation_ft=max(
                        0.0,
                        float(airport.elevation_ft),
                    ),
                )
            )

        return records

    @staticmethod
    def _initial_bearing_deg(
        lat1_deg: float,
        lon1_deg: float,
        lat2_deg: float,
        lon2_deg: float,
    ) -> float:
        lat1 = radians(lat1_deg)
        lat2 = radians(lat2_deg)

        delta_lon = radians(
            lon2_deg - lon1_deg
        )

        y = sin(delta_lon) * cos(lat2)

        x = (
            cos(lat1) * sin(lat2)
            - sin(lat1)
            * cos(lat2)
            * cos(delta_lon)
        )

        return (
            degrees(
                atan2(
                    y,
                    x,
                )
            )
            + 360.0
        ) % 360.0

    @staticmethod
    def _safe_latitude(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        if not -90.0 <= number <= 90.0:
            return None

        return number

    @staticmethod
    def _safe_longitude(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        if not -180.0 <= number <= 180.0:
            return None

        return number