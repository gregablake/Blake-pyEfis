from types import SimpleNamespace

import pytest

from pyefis.user.blake_pfd.core.nearby_airport_provider import (
    NearbyAirportProvider,
)


class FakeDatabase:
    def __init__(self) -> None:
        self.calls: list[tuple[float, float, int]] = []

    def nearest_airports(
        self,
        lat_deg: float,
        lon_deg: float,
        max_results: int = 10,
    ):
        self.calls.append(
            (
                lat_deg,
                lon_deg,
                max_results,
            )
        )

        return [
            (
                5.0,
                SimpleNamespace(
                    ident="NORTH",
                    lat_deg=40.0,
                    lon_deg=-84.0,
                    elevation_ft=700.0,
                ),
            ),
            (
                8.0,
                SimpleNamespace(
                    ident="EAST",
                    lat_deg=39.0,
                    lon_deg=-83.0,
                    elevation_ft=900.0,
                ),
            ),
        ]


def test_provider_converts_database_results() -> None:
    database = FakeDatabase()

    provider = NearbyAirportProvider(
        database=database,
        maximum_results=15,
    )

    results = provider.get_nearby_airports(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
    )

    assert len(results) == 2

    assert results[0].identifier == "NORTH"
    assert results[0].distance_nm == 5.0
    assert results[0].elevation_ft == 700.0

    assert results[1].identifier == "EAST"
    assert results[1].distance_nm == 8.0
    assert results[1].elevation_ft == 900.0

    assert database.calls == [
        (
            39.0,
            -84.0,
            15,
        )
    ]


def test_provider_calculates_north_bearing() -> None:
    database = FakeDatabase()

    provider = NearbyAirportProvider(
        database=database,
    )

    results = provider.get_nearby_airports(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
    )

    assert results[0].bearing_deg == pytest.approx(
        0.0,
        abs=0.1,
    )


def test_provider_calculates_east_bearing() -> None:
    database = FakeDatabase()

    provider = NearbyAirportProvider(
        database=database,
    )

    results = provider.get_nearby_airports(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
    )

    assert results[1].bearing_deg == pytest.approx(
        89.7,
        abs=1.0,
    )


def test_invalid_position_returns_empty_list() -> None:
    database = FakeDatabase()

    provider = NearbyAirportProvider(
        database=database,
    )

    results = provider.get_nearby_airports(
        aircraft_lat_deg=float("nan"),
        aircraft_lon_deg=-84.0,
    )

    assert results == []
    assert database.calls == []


def test_out_of_range_position_returns_empty_list() -> None:
    database = FakeDatabase()

    provider = NearbyAirportProvider(
        database=database,
    )

    assert provider.get_nearby_airports(
        aircraft_lat_deg=91.0,
        aircraft_lon_deg=-84.0,
    ) == []

    assert provider.get_nearby_airports(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-181.0,
    ) == []


def test_negative_distance_and_elevation_are_clamped() -> None:
    database = SimpleNamespace(
        nearest_airports=lambda *args, **kwargs: [
            (
                -2.0,
                SimpleNamespace(
                    ident="TEST",
                    lat_deg=39.1,
                    lon_deg=-84.0,
                    elevation_ft=-100.0,
                ),
            )
        ]
    )

    provider = NearbyAirportProvider(
        database=database,
    )

    result = provider.get_nearby_airports(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
    )[0]

    assert result.distance_nm == 0.0
    assert result.elevation_ft == 0.0


def test_invalid_maximum_results_raises() -> None:
    with pytest.raises(
        ValueError,
        match="maximum_results",
    ):
        NearbyAirportProvider(
            database=FakeDatabase(),
            maximum_results=0,
        )