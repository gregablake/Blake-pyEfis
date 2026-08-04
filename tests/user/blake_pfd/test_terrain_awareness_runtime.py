from pyefis.user.blake_pfd.core.terrain_awareness_manager import (
    TerrainAwarenessManager,
)
from pyefis.user.blake_pfd.core.terrain_profile_provider import (
    TerrainProfileProvider,
)
from pyefis.user.blake_pfd.core.terrain_sampler import (
    TerrainSampler,
)


class RuntimeTerrainSource:
    def get_elevation(
        self,
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        del latitude_deg
        del longitude_deg
        return 1200.0


def test_runtime_pipeline_creates_valid_state() -> None:
    sampler = TerrainSampler(
        terrain=RuntimeTerrainSource(),
    )

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
        sample_distances_nm=(
            1.0,
            3.0,
            5.0,
        ),
    )

    manager = TerrainAwarenessManager(
        profile_provider=provider,
    )

    state = manager.update(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
        aircraft_altitude_ft=5000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=100.0,
        position_valid=True,
    )

    assert state.valid is True
    assert len(state.profile.points) == 3
    assert (
        state.awareness.minimum_clearance_ft
        == 3800.0
    )
    assert (
        state.awareness.warning_level
        == "NONE"
    )


def test_runtime_pipeline_clears_invalid_position() -> None:
    sampler = TerrainSampler(
        terrain=RuntimeTerrainSource(),
    )

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
        sample_distances_nm=(1.0,),
    )

    manager = TerrainAwarenessManager(
        profile_provider=provider,
    )

    manager.update(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
        aircraft_altitude_ft=5000.0,
        ground_speed_kt=100.0,
        position_valid=True,
    )

    manager.clear()

    assert manager.state.valid is False
    assert manager.state.profile.points == ()