from __future__ import annotations

from dataclasses import replace

import pytest

from pyefis.user.blake_pfd.core.runway_geometry import (
    RunwayGeometryComputer,
)
from pyefis.user.blake_pfd.database_importer import (
    AviationDatabase,
)


@pytest.fixture
def khao_runway():
    database = AviationDatabase()
    database.load_runways()

    runways = database.get_runways("KHAO")

    assert len(runways) == 1

    return runways[0]


def test_khao_geometry_preserves_runway_identity(
    khao_runway,
) -> None:
    geometry = RunwayGeometryComputer().compute(
        runway=khao_runway,
        aircraft_lat_deg=39.3638,
        aircraft_lon_deg=-84.5400,
        aircraft_alt_ft=1600.0,
    )

    assert geometry is not None

    assert geometry.airport_ident == "KHAO"
    assert geometry.low_end.ident == "12"
    assert geometry.high_end.ident == "30"

    assert geometry.length_ft == pytest.approx(
        5500.0
    )
    assert geometry.width_ft == pytest.approx(
        100.0
    )


def test_aircraft_west_of_khao_has_runway_to_east(
    khao_runway,
) -> None:
    geometry = RunwayGeometryComputer().compute(
        runway=khao_runway,
        aircraft_lat_deg=39.3638,
        aircraft_lon_deg=-84.5500,
        aircraft_alt_ft=1600.0,
    )

    assert geometry is not None

    assert geometry.low_end.east_ft > 0.0
    assert geometry.high_end.east_ft > 0.0


def test_threshold_below_aircraft_has_negative_up(
    khao_runway,
) -> None:
    geometry = RunwayGeometryComputer().compute(
        runway=khao_runway,
        aircraft_lat_deg=39.3638,
        aircraft_lon_deg=-84.5400,
        aircraft_alt_ft=1600.0,
    )

    assert geometry is not None

    assert geometry.low_end.up_ft == pytest.approx(
        632.0 - 1600.0
    )
    assert geometry.high_end.up_ft == pytest.approx(
        619.0 - 1600.0
    )

    assert geometry.low_end.up_ft < 0.0
    assert geometry.high_end.up_ft < 0.0


def test_missing_threshold_coordinates_fail_closed(
    khao_runway,
) -> None:
    invalid_runway = replace(
        khao_runway,
        le_latitude_deg=None,
    )

    geometry = RunwayGeometryComputer().compute(
        runway=invalid_runway,
        aircraft_lat_deg=39.3638,
        aircraft_lon_deg=-84.5400,
        aircraft_alt_ft=1600.0,
    )

    assert geometry is None


def test_invalid_aircraft_position_fails_closed(
    khao_runway,
) -> None:
    geometry = RunwayGeometryComputer().compute(
        runway=khao_runway,
        aircraft_lat_deg=200.0,
        aircraft_lon_deg=-84.5400,
        aircraft_alt_ft=1600.0,
    )

    assert geometry is None


def test_endpoint_distance_and_bearing_are_sensible(
    khao_runway,
) -> None:
    geometry = RunwayGeometryComputer().compute(
        runway=khao_runway,
        aircraft_lat_deg=39.3638,
        aircraft_lon_deg=-84.5400,
        aircraft_alt_ft=1600.0,
    )

    assert geometry is not None

    assert geometry.low_end.distance_ft > 0.0
    assert geometry.high_end.distance_ft > 0.0

    assert 0.0 <= geometry.low_end.bearing_deg < 360.0
    assert 0.0 <= geometry.high_end.bearing_deg < 360.0
