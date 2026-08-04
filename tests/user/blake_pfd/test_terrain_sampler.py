from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_sampler import (
    TerrainSampler,
)


class FakeElevationTerrain:
    def __init__(self) -> None:
        self.calls: list[
            tuple[float, float]
        ] = []

    def get_elevation(
        self,
        latitude_deg: float,
        longitude_deg: float,
    ) -> float:
        self.calls.append(
            (
                latitude_deg,
                longitude_deg,
            )
        )
        return 1234.5


class FakeUpdateTerrain:
    def __init__(self) -> None:
        self.calls: list[
            tuple[
                float,
                float,
                float,
            ]
        ] = []

    def update(
        self,
        *,
        aircraft_alt_ft: float,
        aircraft_lat: float,
        aircraft_lon: float,
    ):
        self.calls.append(
            (
                aircraft_alt_ft,
                aircraft_lat,
                aircraft_lon,
            )
        )

        return SimpleNamespace(
            terrain_elevation_ft=987.0,
        )


def test_sampler_uses_get_elevation() -> None:
    terrain = FakeElevationTerrain()

    sampler = TerrainSampler(
        terrain=terrain,
    )

    elevation = sampler(
        39.0,
        -84.0,
    )

    assert elevation == 1234.5
    assert terrain.calls == [
        (
            39.0,
            -84.0,
        )
    ]


def test_sampler_falls_back_to_update() -> None:
    terrain = FakeUpdateTerrain()

    sampler = TerrainSampler(
        terrain=terrain,
    )

    elevation = sampler(
        39.0,
        -84.0,
    )

    assert elevation == 987.0
    assert terrain.calls == [
        (
            0.0,
            39.0,
            -84.0,
        )
    ]


def test_none_from_get_elevation_is_forwarded() -> None:
    class EmptyTerrain:
        def get_elevation(
            self,
            latitude_deg: float,
            longitude_deg: float,
        ) -> None:
            del latitude_deg
            del longitude_deg
            return None

    sampler = TerrainSampler(
        terrain=EmptyTerrain(),
    )

    assert sampler(
        39.0,
        -84.0,
    ) is None


def test_missing_terrain_interfaces_returns_none() -> None:
    sampler = TerrainSampler(
        terrain=object(),
    )

    assert sampler(
        39.0,
        -84.0,
    ) is None


def test_update_without_elevation_returns_none() -> None:
    class EmptyUpdateTerrain:
        def update(
            self,
            *,
            aircraft_alt_ft: float,
            aircraft_lat: float,
            aircraft_lon: float,
        ):
            del aircraft_alt_ft
            del aircraft_lat
            del aircraft_lon
            return SimpleNamespace()

    sampler = TerrainSampler(
        terrain=EmptyUpdateTerrain(),
    )

    assert sampler(
        39.0,
        -84.0,
    ) is None