from pyefis.user.blake_pfd.core.terrain_awareness import (
    TerrainAwareness,
)
from pyefis.user.blake_pfd.core.terrain_awareness_manager import (
    TerrainAwarenessManager,
)
from pyefis.user.blake_pfd.core.terrain_profile_provider import (
    TerrainProfileProvider,
)


def test_manager_builds_and_evaluates_profile() -> None:
    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: 1000.0
        ),
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
    assert state.awareness.valid is True
    assert (
        state.awareness.minimum_clearance_ft
        == 4000.0
    )
    assert (
        state.awareness.warning_level
        == "NONE"
    )


def test_manager_produces_terrain_warning() -> None:
    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: 2600.0
        ),
        sample_distances_nm=(2.0,),
    )

    manager = TerrainAwarenessManager(
        profile_provider=provider,
    )

    state = manager.update(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
        aircraft_altitude_ft=3000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=100.0,
    )

    assert state.valid is True
    assert (
        state.awareness.minimum_clearance_ft
        == 400.0
    )
    assert (
        state.awareness.warning_level
        == "WARNING"
    )
    assert (
        state.awareness.message
        == "TERRAIN AHEAD"
    )


def test_manager_projects_descent_into_terrain() -> None:
    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: 3000.0
        ),
        sample_distances_nm=(6.0,),
    )

    manager = TerrainAwarenessManager(
        profile_provider=provider,
    )

    state = manager.update(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
        aircraft_altitude_ft=5000.0,
        vertical_speed_fpm=-1000.0,
        ground_speed_kt=120.0,
    )

    assert state.valid is True
    assert (
        state.awareness.minimum_clearance_ft
        == -1000.0
    )
    assert (
        state.awareness.warning_level
        == "CRITICAL"
    )
    assert state.awareness.message == "PULL UP"


def test_invalid_position_skips_provider() -> None:
    calls = 0

    def sampler(
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        nonlocal calls
        calls += 1
        return 1000.0

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
    )

    manager = TerrainAwarenessManager(
        profile_provider=provider,
    )

    state = manager.update(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
        aircraft_altitude_ft=5000.0,
        position_valid=False,
    )

    assert state.valid is False
    assert (
        state.message
        == "AIRCRAFT POSITION INVALID"
    )
    assert calls == 0


def test_missing_sample_returns_invalid_state() -> None:
    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: None
        ),
        sample_distances_nm=(
            1.0,
            2.0,
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
    )

    assert state.valid is False
    assert (
        state.message
        == "TERRAIN SAMPLE UNAVAILABLE"
    )


def test_custom_awareness_thresholds_are_used() -> None:
    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: 2200.0
        ),
        sample_distances_nm=(2.0,),
    )

    awareness = TerrainAwareness(
        caution_clearance_ft=500.0,
        warning_clearance_ft=300.0,
        critical_clearance_ft=100.0,
    )

    manager = TerrainAwarenessManager(
        profile_provider=provider,
        awareness=awareness,
    )

    state = manager.update(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
        aircraft_altitude_ft=3000.0,
    )

    assert state.valid is True
    assert (
        state.awareness.minimum_clearance_ft
        == 800.0
    )
    assert (
        state.awareness.warning_level
        == "NONE"
    )


def test_clear_resets_manager_state() -> None:
    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: 1000.0
        ),
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
    )

    manager.clear()

    assert manager.state.valid is False
    assert manager.state.profile.points == ()
    assert manager.state.awareness.valid is False