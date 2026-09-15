from types import SimpleNamespace

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


class FakeStratux:
    def __init__(self):
        self.read_count = 0

        self.state = SimpleNamespace(
            uplinks=[
                "UPLINK-A",
                "UPLINK-B",
            ],
        )

    def read(self):
        self.read_count += 1
        return self.state


class FakeWeather:
    def __init__(self):
        self.ingest_count = 0
        self.read_count = 0
        self.last_uplinks = None

        self.state = object()

    def ingest_uplinks(
        self,
        uplinks,
    ):
        self.ingest_count += 1
        self.last_uplinks = list(
            uplinks
        )

    def read(self):
        self.read_count += 1
        return self.state


def test_single_stratux_read_feeds_weather():

    fake_self = SimpleNamespace(
        stratux=FakeStratux(),
        weather=FakeWeather(),
    )

    (
        stratux_state,
        weather_state,
    ) = (
        BlakePfdDemo
        ._read_stratux_weather_states(
            fake_self
        )
    )

    assert (
        fake_self.stratux.read_count
        == 1
    )

    assert (
        fake_self.weather.ingest_count
        == 1
    )

    assert (
        fake_self.weather.read_count
        == 1
    )

    assert (
        fake_self.weather.last_uplinks
        == [
            "UPLINK-A",
            "UPLINK-B",
        ]
    )

    assert (
        stratux_state
        is fake_self.stratux.state
    )

    assert (
        weather_state
        is fake_self.weather.state
    )
