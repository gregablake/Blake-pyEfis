from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite
from pathlib import Path
from struct import unpack_from


METERS_TO_FEET = 3.280839895


@dataclass(frozen=True)
class SrtmTile:
    path: Path
    latitude_deg: int
    longitude_deg: int
    samples_per_side: int
    data: bytes


class SrtmTerrainSource:
    """
    Reads local SRTM .hgt elevation tiles.

    Supported tile sizes:

    - 1201 x 1201 samples: SRTM3
    - 3601 x 3601 samples: SRTM1

    Elevations are stored as signed 16-bit big-endian
    integers in meters.
    """

    VOID_ELEVATION = -32768

    def __init__(
        self,
        terrain_directory: str | Path,
    ) -> None:
        self.terrain_directory = Path(
            terrain_directory
        )

        self._cached_tile_name: str | None = None
        self._cached_tile: SrtmTile | None = None

    def get_elevation(
        self,
        latitude_deg,
        longitude_deg,
    ) -> float | None:
        latitude = self._safe_latitude(
            latitude_deg
        )
        longitude = self._safe_longitude(
            longitude_deg
        )

        if latitude is None or longitude is None:
            return None

        tile_latitude = floor(latitude)
        tile_longitude = floor(longitude)

        tile_name = self.tile_name(
            tile_latitude,
            tile_longitude,
        )

        tile = self._load_tile(
            tile_name=tile_name,
            latitude_deg=tile_latitude,
            longitude_deg=tile_longitude,
        )

        if tile is None:
            return None

        latitude_fraction = (
            latitude - tile_latitude
        )
        longitude_fraction = (
            longitude - tile_longitude
        )

        maximum_index = (
            tile.samples_per_side - 1
        )

        row = int(
            round(
                (1.0 - latitude_fraction)
                * maximum_index
            )
        )

        column = int(
            round(
                longitude_fraction
                * maximum_index
            )
        )

        row = max(
            0,
            min(
                maximum_index,
                row,
            ),
        )

        column = max(
            0,
            min(
                maximum_index,
                column,
            ),
        )

        sample_index = (
            row
            * tile.samples_per_side
            + column
        )

        byte_offset = sample_index * 2

        elevation_m = unpack_from(
            ">h",
            tile.data,
            byte_offset,
        )[0]

        if elevation_m == self.VOID_ELEVATION:
            return None

        return (
            float(elevation_m)
            * METERS_TO_FEET
        )

    def __call__(
        self,
        latitude_deg: float,
        longitude_deg: float,
    ) -> float | None:
        return self.get_elevation(
            latitude_deg,
            longitude_deg,
        )

    def _load_tile(
        self,
        *,
        tile_name: str,
        latitude_deg: int,
        longitude_deg: int,
    ) -> SrtmTile | None:
        if (
            self._cached_tile_name == tile_name
            and self._cached_tile is not None
        ):
            return self._cached_tile

        tile_path = (
            self.terrain_directory
            / f"{tile_name}.hgt"
        )

        if not tile_path.is_file():
            return None

        try:
            data = tile_path.read_bytes()
        except OSError:
            return None

        samples_per_side = (
            self._samples_per_side(
                len(data)
            )
        )

        if samples_per_side is None:
            return None

        tile = SrtmTile(
            path=tile_path,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            samples_per_side=samples_per_side,
            data=data,
        )

        self._cached_tile_name = tile_name
        self._cached_tile = tile

        return tile

    @staticmethod
    def _samples_per_side(
        byte_count: int,
    ) -> int | None:
        if byte_count == 1201 * 1201 * 2:
            return 1201

        if byte_count == 3601 * 3601 * 2:
            return 3601

        return None

    @staticmethod
    def tile_name(
        latitude_deg: int,
        longitude_deg: int,
    ) -> str:
        latitude_prefix = (
            "N"
            if latitude_deg >= 0
            else "S"
        )

        longitude_prefix = (
            "E"
            if longitude_deg >= 0
            else "W"
        )

        return (
            f"{latitude_prefix}"
            f"{abs(latitude_deg):02d}"
            f"{longitude_prefix}"
            f"{abs(longitude_deg):03d}"
        )

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

    @staticmethod
    def _safe_latitude(
        value,
    ) -> float | None:
        latitude = SrtmTerrainSource._safe_number(
            value
        )

        if (
            latitude is None
            or latitude < -90.0
            or latitude > 90.0
        ):
            return None

        return latitude

    @staticmethod
    def _safe_longitude(
        value,
    ) -> float | None:
        longitude = SrtmTerrainSource._safe_number(
            value
        )

        if (
            longitude is None
            or longitude < -180.0
            or longitude > 180.0
        ):
            return None

        return longitude