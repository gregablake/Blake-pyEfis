import pytest

from pyefis.user.blake_pfd.core.terrain_profile_provider import (
    TerrainProfileProvider,
)


def test_builds_profile_from_sampler() -> None:
    calls: list[tuple[float, float]] = []

    def sampler(
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        calls.append(
            (
                latitude_deg,
                longitude_deg,
            )
        )
        return 1200.0 + len(calls) * 100.0

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
        sample_distances_nm=(
            1.0,
            3.0,
            5.0,
        ),
    )

    profile = provider.build_profile(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
    )

    assert profile.valid is True
    assert profile.message == ""
    assert len(profile.points) == 3
    assert len(calls) == 3
    assert profile.points[0].distance_nm == 1.0
    assert profile.points[1].distance_nm == 3.0
    assert profile.points[2].distance_nm == 5.0
    assert profile.points[0].elevation_ft == 1300.0
    assert profile.points[2].elevation_ft == 1500.0


def test_eastbound_samples_move_longitude_east() -> None:
    sampled_positions: list[
        tuple[float, float]
    ] = []

    def sampler(
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        sampled_positions.append(
            (
                latitude_deg,
                longitude_deg,
            )
        )
        return 1000.0

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
        sample_distances_nm=(5.0,),
    )

    profile = provider.build_profile(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
    )

    assert profile.valid is True

    sampled_latitude, sampled_longitude = (
        sampled_positions[0]
    )

    assert sampled_latitude == pytest.approx(
        39.0,
        abs=0.1,
    )
    assert sampled_longitude > -84.0


def test_northbound_samples_move_latitude_north() -> None:
    sampled_positions: list[
        tuple[float, float]
    ] = []

    def sampler(
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        sampled_positions.append(
            (
                latitude_deg,
                longitude_deg,
            )
        )
        return 1000.0

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
        sample_distances_nm=(5.0,),
    )

    profile = provider.build_profile(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=0.0,
    )

    assert profile.valid is True
    assert sampled_positions[0][0] > 39.0


def test_course_is_normalized() -> None:
    sampled_positions: list[
        tuple[float, float]
    ] = []

    def sampler(
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        sampled_positions.append(
            (
                latitude_deg,
                longitude_deg,
            )
        )
        return 1000.0

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
        sample_distances_nm=(5.0,),
    )

    profile = provider.build_profile(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=450.0,
    )

    assert profile.valid is True
    assert sampled_positions[0][1] > -84.0


def test_missing_terrain_sample_returns_invalid_profile() -> None:
    def sampler(
        latitude_deg: float,
        longitude_deg: float,
    ) -> float | None:
        del latitude_deg
        del longitude_deg
        return None

    provider = TerrainProfileProvider(
        elevation_sampler=sampler,
        sample_distances_nm=(
            1.0,
            2.0,
        ),
    )

    profile = provider.build_profile(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
    )

    assert profile.valid is False
    assert profile.message == (
        "TERRAIN SAMPLE UNAVAILABLE"
    )


def test_invalid_position_returns_invalid_profile() -> None:
    provider = TerrainProfileProvider(
        elevation_sampler=(
            lambda latitude, longitude: 1000.0
        ),
    )

    profile = provider.build_profile(
        aircraft_lat_deg=100.0,
        aircraft_lon_deg=-84.0,
        course_deg=90.0,
    )

    assert profile.valid is False
    assert profile.message == (
        "AIRCRAFT POSITION INVALID"
    )


def test_rejects_empty_distance_list() -> None:
    with pytest.raises(ValueError):
        TerrainProfileProvider(
            elevation_sampler=(
                lambda latitude, longitude: 1000.0
            ),
            sample_distances_nm=(),
        )


def test_rejects_nonincreasing_distances() -> None:
    with pytest.raises(ValueError):
        TerrainProfileProvider(
            elevation_sampler=(
                lambda latitude, longitude: 1000.0
            ),
            sample_distances_nm=(
                1.0,
                1.0,
            ),
        )


def test_rejects_negative_distance() -> None:
    with pytest.raises(ValueError):
        TerrainProfileProvider(
            elevation_sampler=(
                lambda latitude, longitude: 1000.0
            ),
            sample_distances_nm=(
                -1.0,
                2.0,
            ),
        )


def test_rejects_noncallable_sampler() -> None:
    with pytest.raises(TypeError):
        TerrainProfileProvider(
            elevation_sampler=None,
        )