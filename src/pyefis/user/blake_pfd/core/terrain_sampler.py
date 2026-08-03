from __future__ import annotations

from pyefis.user.blake_pfd.terrain import (
    TerrainComputer,
)


class TerrainSampler:
    """
    Adapter that converts the existing TerrainComputer
    into the callable interface expected by
    TerrainProfileProvider.

    Later this class will be replaced with
    an SRTM/GeoTIFF terrain database.
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
        elevation = (
            self.terrain.get_elevation(
                latitude_deg,
                longitude_deg,
            )
        )

        if elevation is None:
            return None

        return float(elevation)