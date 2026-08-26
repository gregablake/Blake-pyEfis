from __future__ import annotations

import pytest

from pyefis.user.blake_pfd.database_importer import (
    AviationDatabase,
)


def test_khao_runway_loads_threshold_geometry() -> None:
    database = AviationDatabase()
    database.load_runways()

    runways = database.get_runways("KHAO")

    assert len(runways) == 1

    runway = runways[0]

    assert runway.le_ident == "12"
    assert runway.he_ident == "30"

    assert runway.length_ft == pytest.approx(5500.0)
    assert runway.width_ft == pytest.approx(100.0)

    assert runway.le_latitude_deg == pytest.approx(
        39.366402
    )
    assert runway.le_longitude_deg == pytest.approx(
        -84.531097
    )
    assert runway.le_elevation_ft == pytest.approx(
        632.0
    )
    assert runway.le_heading_deg == pytest.approx(
        120.0
    )

    assert runway.he_latitude_deg == pytest.approx(
        39.361099
    )
    assert runway.he_longitude_deg == pytest.approx(
        -84.512802
    )
    assert runway.he_elevation_ft == pytest.approx(
        619.0
    )
    assert runway.he_heading_deg == pytest.approx(
        300.0
    )

    assert runway.le_displaced_threshold_ft is None
    assert runway.he_displaced_threshold_ft is None


def test_blank_threshold_geometry_loads_as_none() -> None:
    database = AviationDatabase()
    database.load_runways()

    runways = database.get_runways("00A")

    assert runways

    runway = runways[0]

    assert runway.le_latitude_deg is None
    assert runway.le_longitude_deg is None
    assert runway.le_elevation_ft is None
    assert runway.le_heading_deg is None

    assert runway.he_latitude_deg is None
    assert runway.he_longitude_deg is None
    assert runway.he_elevation_ft is None
    assert runway.he_heading_deg is None
