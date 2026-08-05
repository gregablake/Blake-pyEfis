from pathlib import Path
from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_alert_gate import (
    TerrainAlertGate,
)
from pyefis.user.blake_pfd.core.terrain_awareness_manager import (
    TerrainAwarenessManager,
)
from pyefis.user.blake_pfd.core.terrain_profile_provider import (
    TerrainProfileProvider,
)
from pyefis.user.blake_pfd.core.terrain_startup_validator import (
    TerrainStartupValidator,
)


def create_valid_tile(
    directory: Path,
    tile_name: str,
) -> None:
    path = directory / f"{tile_name}.hgt"

    path.write_bytes(
        b"\x00\x00"
        * (
            1201
            * 1201
        )
    )


def test_real_terrain_warning_passes_gate(
    tmp_path: Path,
) -> None:
    create_valid_tile(
        tmp_path,
        "N39W085",
    )

    config = SimpleNamespace(
        source="srtm",
        srtm_directory=str(tmp_path),
    )

    startup_status = (
        TerrainStartupValidator().validate(
            terrain_config=config,
            aircraft_lat_deg=39.5,
            aircraft_lon_deg=-84.5,
        )
    )

    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: 2600.0
        ),
        sample_distances_nm=(2.0,),
    )

    manager = TerrainAwarenessManager(
        profile_provider=provider,
    )

    awareness_state = manager.update(
        aircraft_lat_deg=39.5,
        aircraft_lon_deg=-84.5,
        course_deg=90.0,
        aircraft_altitude_ft=3000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=100.0,
        position_valid=True,
    )

    alert_state = TerrainAlertGate().evaluate(
        startup_status=startup_status,
        terrain_awareness_state=(
            awareness_state
        ),
        real_terrain_enabled=True,
    )

    assert startup_status.valid is True
    assert alert_state.active is True
    assert alert_state.warning_level == "WARNING"
    assert alert_state.message == "TERRAIN AHEAD"


def test_missing_tile_suppresses_warning(
    tmp_path: Path,
) -> None:
    config = SimpleNamespace(
        source="srtm",
        srtm_directory=str(tmp_path),
    )

    startup_status = (
        TerrainStartupValidator().validate(
            terrain_config=config,
            aircraft_lat_deg=39.5,
            aircraft_lon_deg=-84.5,
        )
    )

    awareness_state = SimpleNamespace(
        valid=True,
        message="",
        awareness=SimpleNamespace(
            valid=True,
            warning_level="CRITICAL",
            message="PULL UP",
            minimum_clearance_ft=-100.0,
        ),
    )

    alert_state = TerrainAlertGate().evaluate(
        startup_status=startup_status,
        terrain_awareness_state=(
            awareness_state
        ),
        real_terrain_enabled=True,
    )

    assert startup_status.valid is False
    assert alert_state.active is False
    assert (
        alert_state.predictive_alerts_enabled
        is False
    )
    assert (
        "SRTM TILE N39W085 MISSING"
        in alert_state.suppressed_reason
    )


def test_fallback_runtime_suppresses_warning() -> None:
    startup_status = (
        TerrainStartupValidator().validate(
            terrain_config=SimpleNamespace(
                source="fallback",
                srtm_directory="",
            ),
        )
    )

    awareness_state = SimpleNamespace(
        valid=True,
        awareness=SimpleNamespace(
            valid=True,
            warning_level="CRITICAL",
            message="PULL UP",
            minimum_clearance_ft=-100.0,
        ),
    )

    alert_state = TerrainAlertGate().evaluate(
        startup_status=startup_status,
        terrain_awareness_state=(
            awareness_state
        ),
        real_terrain_enabled=False,
    )

    assert alert_state.active is False
    assert (
        alert_state.suppressed_reason
        == "REAL TERRAIN DATA NOT ENABLED"
    )