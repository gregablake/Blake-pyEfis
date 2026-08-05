from pathlib import Path
from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_startup_validator import (
    TerrainStartupValidator,
)


def config(
    *,
    source: str = "fallback",
    srtm_directory: str = "",
):
    return SimpleNamespace(
        source=source,
        srtm_directory=srtm_directory,
    )


def create_valid_srtm3_tile(
    directory: Path,
    tile_name: str,
) -> Path:
    path = (
        directory
        / f"{tile_name}.hgt"
    )

    path.write_bytes(
        b"\x00\x00"
        * (
            1201
            * 1201
        )
    )

    return path


def test_fallback_disables_predictive_alerts() -> None:
    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(),
    )

    assert status.valid is True
    assert status.source_name == "fallback"
    assert (
        status.predictive_alerts_enabled
        is False
    )
    assert (
        "PREDICTIVE TERRAIN ALERTS DISABLED"
        in status.message
    )


def test_unknown_source_is_invalid() -> None:
    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(
            source="mystery",
        ),
    )

    assert status.valid is False
    assert (
        status.predictive_alerts_enabled
        is False
    )
    assert (
        status.message
        == "UNKNOWN TERRAIN SOURCE MYSTERY"
    )


def test_missing_srtm_configuration() -> None:
    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(
            source="srtm",
            srtm_directory="",
        ),
    )

    assert status.valid is False
    assert (
        status.message
        == "SRTM DIRECTORY NOT CONFIGURED"
    )


def test_missing_srtm_directory(
    tmp_path: Path,
) -> None:
    validator = TerrainStartupValidator()

    missing_directory = (
        tmp_path
        / "missing"
    )

    status = validator.validate(
        terrain_config=config(
            source="srtm",
            srtm_directory=str(
                missing_directory
            ),
        ),
    )

    assert status.valid is False
    assert status.directory_exists is False
    assert (
        status.message
        == "SRTM DIRECTORY NOT FOUND"
    )


def test_empty_srtm_directory(
    tmp_path: Path,
) -> None:
    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(
            source="srtm",
            srtm_directory=str(
                tmp_path
            ),
        ),
    )

    assert status.valid is False
    assert status.directory_exists is True
    assert status.tile_available is False
    assert (
        status.message
        == "SRTM DIRECTORY CONTAINS "
        "NO TERRAIN TILES"
    )


def test_directory_with_tile_is_ready_without_position(
    tmp_path: Path,
) -> None:
    create_valid_srtm3_tile(
        tmp_path,
        "N39W085",
    )

    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(
            source="srtm",
            srtm_directory=str(
                tmp_path
            ),
        ),
    )

    assert status.valid is True
    assert status.tile_available is True
    assert (
        status.predictive_alerts_enabled
        is True
    )
    assert status.message == "SRTM TERRAIN READY"


def test_matching_position_tile_is_ready(
    tmp_path: Path,
) -> None:
    create_valid_srtm3_tile(
        tmp_path,
        "N39W085",
    )

    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(
            source="srtm",
            srtm_directory=str(
                tmp_path
            ),
        ),
        aircraft_lat_deg=39.5,
        aircraft_lon_deg=-84.5,
    )

    assert status.valid is True
    assert status.tile_available is True
    assert (
        status.predictive_alerts_enabled
        is True
    )
    assert (
        status.message
        == "SRTM TILE N39W085 READY"
    )


def test_missing_position_tile_disables_alerts(
    tmp_path: Path,
) -> None:
    create_valid_srtm3_tile(
        tmp_path,
        "N38W085",
    )

    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(
            source="srtm",
            srtm_directory=str(
                tmp_path
            ),
        ),
        aircraft_lat_deg=39.5,
        aircraft_lon_deg=-84.5,
    )

    assert status.valid is False
    assert status.tile_available is False
    assert (
        status.predictive_alerts_enabled
        is False
    )
    assert (
        status.message
        == "SRTM TILE N39W085 MISSING"
    )


def test_invalid_tile_size_disables_alerts(
    tmp_path: Path,
) -> None:
    invalid_tile = (
        tmp_path
        / "N39W085.hgt"
    )

    invalid_tile.write_bytes(
        b"invalid"
    )

    validator = TerrainStartupValidator()

    status = validator.validate(
        terrain_config=config(
            source="srtm",
            srtm_directory=str(
                tmp_path
            ),
        ),
        aircraft_lat_deg=39.5,
        aircraft_lon_deg=-84.5,
    )

    assert status.valid is False
    assert status.tile_available is False
    assert (
        status.predictive_alerts_enabled
        is False
    )
    assert (
        status.message
        == "SRTM TILE N39W085 INVALID"
    )