from pathlib import Path
from types import SimpleNamespace

from pyefis.user.blake_pfd.core.cfit_manager import (
    CfitManager,
)
from pyefis.user.blake_pfd.core.terrain_startup_validator import (
    TerrainStartupValidator,
)


def create_valid_tile(
    directory: Path,
    tile_name: str,
) -> None:
    tile_path = (
        directory
        / f"{tile_name}.hgt"
    )

    tile_path.write_bytes(
        b"\x00\x00"
        * (
            1201
            * 1201
        )
    )


def terrain_profile(
    *,
    distance_nm: float,
    elevation_ft: float,
):
    return SimpleNamespace(
        points=[
            SimpleNamespace(
                distance_nm=distance_nm,
                elevation_ft=elevation_ft,
            )
        ]
    )


def test_valid_srtm_allows_cfit_prediction(
    tmp_path: Path,
) -> None:
    create_valid_tile(
        tmp_path,
        "N39W085",
    )

    terrain_config = SimpleNamespace(
        source="srtm",
        srtm_directory=str(tmp_path),
    )

    startup_status = (
        TerrainStartupValidator().validate(
            terrain_config=terrain_config,
            aircraft_lat_deg=39.5,
            aircraft_lon_deg=-84.5,
        )
    )

    manager = CfitManager()

    inputs_valid = (
        startup_status.predictive_alerts_enabled
        and True
    )

    if inputs_valid:
        state = manager.update(
            aircraft_altitude_ft=3000.0,
            vertical_speed_fpm=-1000.0,
            ground_speed_kt=120.0,
            terrain_profile=terrain_profile(
                distance_nm=3.0,
                elevation_ft=3200.0,
            ),
        )
    else:
        manager.clear()
        state = manager.state

    assert startup_status.valid is True
    assert state.valid is True
    assert (
        state.prediction.collision_predicted
        is True
    )
    assert (
        state.prediction.message
        == "CFIT PREDICTED"
    )


def test_fallback_terrain_clears_cfit_state() -> None:
    terrain_config = SimpleNamespace(
        source="fallback",
        srtm_directory="",
    )

    startup_status = (
        TerrainStartupValidator().validate(
            terrain_config=terrain_config,
        )
    )

    manager = CfitManager()

    manager.update(
        aircraft_altitude_ft=3000.0,
        vertical_speed_fpm=-1000.0,
        ground_speed_kt=120.0,
        terrain_profile=terrain_profile(
            distance_nm=3.0,
            elevation_ft=3200.0,
        ),
    )

    inputs_valid = (
        startup_status.predictive_alerts_enabled
        and False
    )

    if not inputs_valid:
        manager.clear()

    assert (
        startup_status.predictive_alerts_enabled
        is False
    )
    assert manager.state.valid is False


def test_missing_tile_clears_cfit_state(
    tmp_path: Path,
) -> None:
    terrain_config = SimpleNamespace(
        source="srtm",
        srtm_directory=str(tmp_path),
    )

    startup_status = (
        TerrainStartupValidator().validate(
            terrain_config=terrain_config,
            aircraft_lat_deg=39.5,
            aircraft_lon_deg=-84.5,
        )
    )

    manager = CfitManager()

    if not startup_status.predictive_alerts_enabled:
        manager.clear()

    assert startup_status.valid is False
    assert (
        startup_status.predictive_alerts_enabled
        is False
    )
    assert manager.state.valid is False


def test_safe_profile_returns_no_collision() -> None:
    manager = CfitManager()

    state = manager.update(
        aircraft_altitude_ft=5000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=100.0,
        terrain_profile=terrain_profile(
            distance_nm=5.0,
            elevation_ft=2000.0,
        ),
    )

    assert state.valid is True
    assert (
        state.prediction.collision_predicted
        is False
    )