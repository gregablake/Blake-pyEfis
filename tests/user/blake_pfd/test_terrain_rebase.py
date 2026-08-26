from __future__ import annotations

import pytest

from pyefis.user.blake_pfd.core.terrain_rebase import (
    TerrainSurfaceRebaser,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
    TerrainSurfaceVertex,
    TerrainTriangle,
)


def _surface() -> TerrainSurface:
    return TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=999.0,
                east_ft=999.0,
                up_ft=999.0,
                latitude_deg=39.0000,
                longitude_deg=-84.0000,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=999.0,
                east_ft=999.0,
                up_ft=999.0,
                latitude_deg=39.0100,
                longitude_deg=-84.0000,
                elevation_ft=1200.0,
            ),
            TerrainSurfaceVertex(
                north_ft=999.0,
                east_ft=999.0,
                up_ft=999.0,
                latitude_deg=39.0000,
                longitude_deg=-83.9900,
                elevation_ft=900.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
        ),
        rows=1,
        columns=3,
        valid=True,
    )


def test_vertex_at_aircraft_position_rebases_to_origin() -> None:
    rebased = TerrainSurfaceRebaser().rebase(
        surface=_surface(),
        aircraft_lat_deg=39.0000,
        aircraft_lon_deg=-84.0000,
        aircraft_alt_ft=1000.0,
    )

    assert rebased.valid is True

    vertex = rebased.vertices[0]

    assert vertex.north_ft == pytest.approx(
        0.0,
        abs=0.1,
    )
    assert vertex.east_ft == pytest.approx(
        0.0,
        abs=0.1,
    )
    assert vertex.up_ft == pytest.approx(0.0)


def test_northern_vertex_rebases_north_of_aircraft() -> None:
    rebased = TerrainSurfaceRebaser().rebase(
        surface=_surface(),
        aircraft_lat_deg=39.0000,
        aircraft_lon_deg=-84.0000,
        aircraft_alt_ft=1000.0,
    )

    vertex = rebased.vertices[1]

    assert vertex.north_ft > 0.0
    assert abs(vertex.east_ft) < 20.0


def test_eastern_vertex_rebases_east_of_aircraft() -> None:
    rebased = TerrainSurfaceRebaser().rebase(
        surface=_surface(),
        aircraft_lat_deg=39.0000,
        aircraft_lon_deg=-84.0000,
        aircraft_alt_ft=1000.0,
    )

    vertex = rebased.vertices[2]

    assert vertex.east_ft > 0.0
    assert abs(vertex.north_ft) < 20.0


def test_aircraft_movement_changes_relative_position() -> None:
    rebaser = TerrainSurfaceRebaser()

    first = rebaser.rebase(
        surface=_surface(),
        aircraft_lat_deg=39.0000,
        aircraft_lon_deg=-84.0000,
        aircraft_alt_ft=1000.0,
    )

    second = rebaser.rebase(
        surface=_surface(),
        aircraft_lat_deg=39.0050,
        aircraft_lon_deg=-84.0000,
        aircraft_alt_ft=1000.0,
    )

    assert (
        second.vertices[1].north_ft
        < first.vertices[1].north_ft
    )


def test_current_altitude_rebases_vertical_coordinate() -> None:
    rebased = TerrainSurfaceRebaser().rebase(
        surface=_surface(),
        aircraft_lat_deg=39.0000,
        aircraft_lon_deg=-84.0000,
        aircraft_alt_ft=1100.0,
    )

    assert rebased.vertices[0].up_ft == pytest.approx(
        -100.0
    )
    assert rebased.vertices[1].up_ft == pytest.approx(
        100.0
    )


def test_rebase_preserves_geography_and_topology() -> None:
    source = _surface()

    rebased = TerrainSurfaceRebaser().rebase(
        surface=source,
        aircraft_lat_deg=39.0000,
        aircraft_lon_deg=-84.0000,
        aircraft_alt_ft=1000.0,
    )

    assert rebased.triangles == source.triangles
    assert rebased.rows == source.rows
    assert rebased.columns == source.columns

    for source_vertex, rebased_vertex in zip(
        source.vertices,
        rebased.vertices,
        strict=True,
    ):
        assert (
            rebased_vertex.latitude_deg
            == source_vertex.latitude_deg
        )
        assert (
            rebased_vertex.longitude_deg
            == source_vertex.longitude_deg
        )
        assert (
            rebased_vertex.elevation_ft
            == source_vertex.elevation_ft
        )


def test_invalid_surface_fails_closed() -> None:
    rebased = TerrainSurfaceRebaser().rebase(
        surface=TerrainSurface(),
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1000.0,
    )

    assert rebased.valid is False


def test_invalid_aircraft_input_fails_closed() -> None:
    rebased = TerrainSurfaceRebaser().rebase(
        surface=_surface(),
        aircraft_lat_deg=float("nan"),
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1000.0,
    )

    assert rebased.valid is False
