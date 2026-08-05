from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite
from pathlib import Path
from typing import Any

from pyefis.user.blake_pfd.core.srtm_terrain_source import (
    SrtmTerrainSource,
)


@dataclass(frozen=True)
class TerrainStartupStatus:
    source_name: str = "fallback"
    configured: bool = False
    directory_exists: bool = False
    tile_available: bool = False
    predictive_alerts_enabled: bool = False
    message: str = ""
    valid: bool = False


class TerrainStartupValidator:
    def validate(
        self,
        *,
        terrain_config: Any,
        aircraft_lat_deg=None,
        aircraft_lon_deg=None,
    ) -> TerrainStartupStatus:
        source_name = str(
            getattr(
                terrain_config,
                "source",
                "fallback",
            )
        ).strip().lower()

        if source_name in {
            "",
            "fallback",
        }:
            return TerrainStartupStatus(
                source_name="fallback",
                configured=True,
                directory_exists=False,
                tile_available=False,
                predictive_alerts_enabled=False,
                message=(
                    "FALLBACK TERRAIN ACTIVE; "
                    "PREDICTIVE TERRAIN ALERTS DISABLED"
                ),
                valid=True,
            )

        if source_name != "srtm":
            return TerrainStartupStatus(
                source_name=source_name,
                configured=False,
                directory_exists=False,
                tile_available=False,
                predictive_alerts_enabled=False,
                message=(
                    f"UNKNOWN TERRAIN SOURCE "
                    f"{source_name.upper()}"
                ),
                valid=False,
            )

        directory_text = str(
            getattr(
                terrain_config,
                "srtm_directory",
                "",
            )
        ).strip()

        if not directory_text:
            return TerrainStartupStatus(
                source_name="srtm",
                configured=False,
                directory_exists=False,
                tile_available=False,
                predictive_alerts_enabled=False,
                message="SRTM DIRECTORY NOT CONFIGURED",
                valid=False,
            )

        directory = Path(
            directory_text
        ).expanduser()

        if not directory.is_dir():
            return TerrainStartupStatus(
                source_name="srtm",
                configured=True,
                directory_exists=False,
                tile_available=False,
                predictive_alerts_enabled=False,
                message="SRTM DIRECTORY NOT FOUND",
                valid=False,
            )

        latitude = self._safe_latitude(
            aircraft_lat_deg
        )
        longitude = self._safe_longitude(
            aircraft_lon_deg
        )

        if latitude is None or longitude is None:
            tile_files = tuple(
                directory.glob("*.hgt")
            )

            if not tile_files:
                return TerrainStartupStatus(
                    source_name="srtm",
                    configured=True,
                    directory_exists=True,
                    tile_available=False,
                    predictive_alerts_enabled=False,
                    message=(
                        "SRTM DIRECTORY CONTAINS "
                        "NO TERRAIN TILES"
                    ),
                    valid=False,
                )

            return TerrainStartupStatus(
                source_name="srtm",
                configured=True,
                directory_exists=True,
                tile_available=True,
                predictive_alerts_enabled=True,
                message="SRTM TERRAIN READY",
                valid=True,
            )

        tile_latitude = floor(
            latitude
        )
        tile_longitude = floor(
            longitude
        )

        tile_name = SrtmTerrainSource.tile_name(
            tile_latitude,
            tile_longitude,
        )

        tile_path = (
            directory
            / f"{tile_name}.hgt"
        )

        if not tile_path.is_file():
            return TerrainStartupStatus(
                source_name="srtm",
                configured=True,
                directory_exists=True,
                tile_available=False,
                predictive_alerts_enabled=False,
                message=(
                    f"SRTM TILE {tile_name} MISSING"
                ),
                valid=False,
            )

        if not self._valid_tile_size(
            tile_path
        ):
            return TerrainStartupStatus(
                source_name="srtm",
                configured=True,
                directory_exists=True,
                tile_available=False,
                predictive_alerts_enabled=False,
                message=(
                    f"SRTM TILE {tile_name} INVALID"
                ),
                valid=False,
            )

        return TerrainStartupStatus(
            source_name="srtm",
            configured=True,
            directory_exists=True,
            tile_available=True,
            predictive_alerts_enabled=True,
            message=(
                f"SRTM TILE {tile_name} READY"
            ),
            valid=True,
        )

    @staticmethod
    def _valid_tile_size(
        path: Path,
    ) -> bool:
        try:
            byte_count = path.stat().st_size
        except OSError:
            return False

        return byte_count in {
            1201 * 1201 * 2,
            3601 * 3601 * 2,
        }

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
        latitude = (
            TerrainStartupValidator
            ._safe_number(
                value
            )
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
        longitude = (
            TerrainStartupValidator
            ._safe_number(
                value
            )
        )

        if (
            longitude is None
            or longitude < -180.0
            or longitude > 180.0
        ):
            return None

        return longitude