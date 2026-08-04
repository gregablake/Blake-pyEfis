from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyefis.user.blake_pfd.core.srtm_terrain_source import (
    SrtmTerrainSource,
)
from pyefis.user.blake_pfd.core.terrain_sampler import (
    TerrainSampler,
)


@dataclass(frozen=True)
class TerrainSourceBundle:
    sampler: TerrainSampler
    source_name: str = "fallback"
    real_terrain_enabled: bool = False
    message: str = ""


def build_terrain_source(
    *,
    terrain_config: Any,
    fallback_terrain: Any,
) -> TerrainSourceBundle:
    source_name = str(
        getattr(
            terrain_config,
            "source",
            "fallback",
        )
    ).strip().lower()

    if source_name == "srtm":
        srtm_directory_text = str(
            getattr(
                terrain_config,
                "srtm_directory",
                "",
            )
        ).strip()

        if not srtm_directory_text:
            return _fallback_bundle(
                fallback_terrain=fallback_terrain,
                message=(
                    "SRTM DIRECTORY NOT CONFIGURED; "
                    "USING FALLBACK TERRAIN"
                ),
            )

        srtm_directory = Path(
            srtm_directory_text
        ).expanduser()

        if not srtm_directory.is_dir():
            return _fallback_bundle(
                fallback_terrain=fallback_terrain,
                message=(
                    "SRTM DIRECTORY NOT FOUND; "
                    "USING FALLBACK TERRAIN"
                ),
            )

        source = SrtmTerrainSource(
            terrain_directory=srtm_directory,
        )

        return TerrainSourceBundle(
            sampler=TerrainSampler(
                terrain=source,
            ),
            source_name="srtm",
            real_terrain_enabled=True,
            message="SRTM TERRAIN ENABLED",
        )

    if source_name not in {
        "",
        "fallback",
    }:
        return _fallback_bundle(
            fallback_terrain=fallback_terrain,
            message=(
                f"UNKNOWN TERRAIN SOURCE "
                f"{source_name.upper()}; "
                "USING FALLBACK TERRAIN"
            ),
        )

    return _fallback_bundle(
        fallback_terrain=fallback_terrain,
        message="FALLBACK TERRAIN ENABLED",
    )


def _fallback_bundle(
    *,
    fallback_terrain: Any,
    message: str,
) -> TerrainSourceBundle:
    return TerrainSourceBundle(
        sampler=TerrainSampler(
            terrain=fallback_terrain,
        ),
        source_name="fallback",
        real_terrain_enabled=False,
        message=message,
    )