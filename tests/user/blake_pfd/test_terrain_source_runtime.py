from pathlib import Path
from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_source_factory import (
    build_terrain_source,
)


class FakeFallbackTerrain:
    def get_elevation(
        self,
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        del latitude_deg
        del longitude_deg
        return 700.0


def test_runtime_uses_fallback_by_default() -> None:
    config = SimpleNamespace(
        source="fallback",
        srtm_directory="",
    )

    bundle = build_terrain_source(
        terrain_config=config,
        fallback_terrain=FakeFallbackTerrain(),
    )

    assert bundle.source_name == "fallback"
    assert bundle.real_terrain_enabled is False
    assert bundle.sampler(
        39.0,
        -84.0,
    ) == 700.0


def test_runtime_uses_srtm_when_configured(
    tmp_path: Path,
) -> None:
    config = SimpleNamespace(
        source="srtm",
        srtm_directory=str(tmp_path),
    )

    bundle = build_terrain_source(
        terrain_config=config,
        fallback_terrain=FakeFallbackTerrain(),
    )

    assert bundle.source_name == "srtm"
    assert bundle.real_terrain_enabled is True
    assert bundle.message == "SRTM TERRAIN ENABLED"