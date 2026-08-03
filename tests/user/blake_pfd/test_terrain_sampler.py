from pyefis.user.blake_pfd.core.terrain_sampler import (
    TerrainSampler,
)


class FakeTerrain:
    def __init__(self):
        self.calls = []

    def get_elevation(
        self,
        lat,
        lon,
    ):
        self.calls.append(
            (lat, lon)
        )
        return 1234.5


def test_sampler_returns_elevation():
    terrain = FakeTerrain()

    sampler = TerrainSampler(
        terrain=terrain
    )

    elevation = sampler(
        39.0,
        -84.0,
    )

    assert elevation == 1234.5
    assert len(terrain.calls) == 1


def test_none_is_forwarded():
    class EmptyTerrain:
        def get_elevation(
            self,
            lat,
            lon,
        ):
            return None

    sampler = TerrainSampler(
        terrain=EmptyTerrain()
    )

    assert sampler(
        39.0,
        -84.0,
    ) is None