from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from pyefis.user.blake_pfd.nav_math import (
    bearing_between_points_deg,
    distance_between_points_nm,
)


@dataclass(frozen=True)
class DirectToState:
    active: bool = False
    identifier: str | None = None
    name: str = ""
    target_lat_deg: float | None = None
    target_lon_deg: float | None = None
    bearing_deg: float | None = None
    distance_nm: float | None = None


class DirectToManager:
    def __init__(self) -> None:
        self.state = DirectToState()

    def activate(
        self,
        *,
        aircraft_lat_deg,
        aircraft_lon_deg,
        target_identifier,
        target_name,
        target_lat_deg,
        target_lon_deg,
    ) -> DirectToState:
        aircraft_lat = self._safe_number(
            aircraft_lat_deg
        )

        aircraft_lon = self._safe_number(
            aircraft_lon_deg
        )

        target_lat = self._safe_number(
            target_lat_deg
        )

        target_lon = self._safe_number(
            target_lon_deg
        )

        if (
            aircraft_lat is None
            or aircraft_lon is None
            or target_lat is None
            or target_lon is None
        ):
            return self.clear()

        identifier = str(
            target_identifier
        ).strip().upper()

        if not identifier:
            return self.clear()

        bearing_deg = (
            bearing_between_points_deg(
                aircraft_lat,
                aircraft_lon,
                target_lat,
                target_lon,
            )
        )

        distance_nm = (
            distance_between_points_nm(
                aircraft_lat,
                aircraft_lon,
                target_lat,
                target_lon,
            )
        )

        self.state = DirectToState(
            active=True,
            identifier=identifier,
            name=str(
                target_name
            ),
            target_lat_deg=target_lat,
            target_lon_deg=target_lon,
            bearing_deg=bearing_deg,
            distance_nm=distance_nm,
        )

        return self.state

    def update(
        self,
        *,
        aircraft_lat_deg,
        aircraft_lon_deg,
    ) -> DirectToState:
        if not self.state.active:
            return self.state

        aircraft_lat = self._safe_number(
            aircraft_lat_deg
        )

        aircraft_lon = self._safe_number(
            aircraft_lon_deg
        )

        target_lat = self.state.target_lat_deg
        target_lon = self.state.target_lon_deg

        if (
            aircraft_lat is None
            or aircraft_lon is None
            or target_lat is None
            or target_lon is None
        ):
            return self.state

        bearing_deg = (
            bearing_between_points_deg(
                aircraft_lat,
                aircraft_lon,
                target_lat,
                target_lon,
            )
        )

        distance_nm = (
            distance_between_points_nm(
                aircraft_lat,
                aircraft_lon,
                target_lat,
                target_lon,
            )
        )

        self.state = DirectToState(
            active=True,
            identifier=self.state.identifier,
            name=self.state.name,
            target_lat_deg=target_lat,
            target_lon_deg=target_lon,
            bearing_deg=bearing_deg,
            distance_nm=distance_nm,
        )

        return self.state

    def clear(
        self,
    ) -> DirectToState:
        self.state = DirectToState()
        return self.state

    @staticmethod
    def _safe_number(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return number