from __future__ import annotations

from pyefis.user.blake_pfd.terrain import (
    TerrainComputer,
)


class TerrainSampler:
    """
    Adapter that exposes terrain elevation through the
    callable interface expected by TerrainProfileProvider.

    It supports both:

    1. Future terrain providers with get_elevation(lat, lon)
    2. The current TerrainComputer with update(...)
    """

    def __init__(
        self,
        terrain: TerrainComputer | None = None,
    ) -> None:
        self.terrain = (
            terrain
            if terrain is not None
            else TerrainComputer()
        )

    def __call__(
        self,
        latitude_deg: float,
        longitude_deg: float,
    ) -> float | None:
        get_elevation = getattr(
            self.terrain,
            "get_elevation",
            None,
        )

        if callable(get_elevation):
            elevation = get_elevation(
                latitude_deg,
                longitude_deg,
            )

            if elevation is None:
                return None

            return float(elevation)

        update = getattr(
            self.terrain,
            "update",
            None,
        )

        if not callable(update):
            return None

        terrain_state = update(
            aircraft_alt_ft=0.0,
            aircraft_lat=latitude_deg,
            aircraft_lon=longitude_deg,
        )

        elevation = getattr(
            terrain_state,
            "terrain_elevation_ft",
            None,
        )

        if elevation is None:
            return None

        return float(elevation)