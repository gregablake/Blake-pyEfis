from pathlib import Path
from types import SimpleNamespace

from pyefis.user.blake_pfd.core.srtm_terrain_source import (
    SrtmTerrainSource,
)
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


def terrain_config(
    *,
    source: str = "fallback",
    srtm_directory: str = "",
):
    return SimpleNamespace(
        source=source,
        srtm_directory=srtm_directory,
    )


def test_fallback_source_is_selected() -> None:
    fallback = FakeFallbackTerrain()

    bundle = build_terrain_source(
        terrain_config=terrain_config(),
        fallback_terrain=fallback,
    )

    assert bundle.source_name == "fallback"
    assert bundle.real_terrain_enabled is False
    assert bundle.message == (
        "FALLBACK TERRAIN ENABLED"
    )
    assert bundle.sampler.terrain is fallback


def test_srtm_source_is_selected(
    tmp_path: Path,
) -> None:
    fallback = FakeFallbackTerrain()

    bundle = build_terrain_source(
        terrain_config=terrain_config(
            source="srtm",
            srtm_directory=str(tmp_path),
        ),
        fallback_terrain=fallback,
    )

    assert bundle.source_name == "srtm"
    assert bundle.real_terrain_enabled is True
    assert bundle.message == (
        "SRTM TERRAIN ENABLED"
    )
    assert isinstance(
        bundle.sampler.terrain,
        SrtmTerrainSource,
    )


def test_blank_srtm_directory_uses_fallback() -> None:
    fallback = FakeFallbackTerrain()

    bundle = build_terrain_source(
        terrain_config=terrain_config(
            source="srtm",
            srtm_directory="",
        ),
        fallback_terrain=fallback,
    )

    assert bundle.source_name == "fallback"
    assert bundle.real_terrain_enabled is False
    assert bundle.sampler.terrain is fallback
    assert (
        "SRTM DIRECTORY NOT CONFIGURED"
        in bundle.message
    )


def test_missing_srtm_directory_uses_fallback(
    tmp_path: Path,
) -> None:
    fallback = FakeFallbackTerrain()

    missing_directory = (
        tmp_path
        / "missing"
    )

    bundle = build_terrain_source(
        terrain_config=terrain_config(
            source="srtm",
            srtm_directory=str(
                missing_directory
            ),
        ),
        fallback_terrain=fallback,
    )

    assert bundle.source_name == "fallback"
    assert bundle.real_terrain_enabled is False
    assert bundle.sampler.terrain is fallback
    assert (
        "SRTM DIRECTORY NOT FOUND"
        in bundle.message
    )


def test_unknown_source_uses_fallback() -> None:
    fallback = FakeFallbackTerrain()

    bundle = build_terrain_source(
        terrain_config=terrain_config(
            source="mystery",
        ),
        fallback_terrain=fallback,
    )

    assert bundle.source_name == "fallback"
    assert bundle.real_terrain_enabled is False
    assert bundle.sampler.terrain is fallback
    assert (
        "UNKNOWN TERRAIN SOURCE MYSTERY"
        in bundle.message
    )


def test_source_name_is_case_insensitive(
    tmp_path: Path,
) -> None:
    bundle = build_terrain_source(
        terrain_config=terrain_config(
            source=" SRTM ",
            srtm_directory=str(tmp_path),
        ),
        fallback_terrain=FakeFallbackTerrain(),
    )

    assert bundle.source_name == "srtm"
    assert bundle.real_terrain_enabled is True


def test_selected_sampler_is_callable(
    tmp_path: Path,
) -> None:
    fallback = FakeFallbackTerrain()

    bundle = build_terrain_source(
        terrain_config=terrain_config(
            source="fallback",
        ),
        fallback_terrain=fallback,
    )

    assert bundle.sampler(
        39.0,
        -84.0,
    ) == 700.0