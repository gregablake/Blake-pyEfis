from __future__ import annotations

from pyefis.user.blake_pfd.core.terrain_projection import (
    TerrainProjectionComputer,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
    TerrainSurfaceVertex,
    TerrainTriangle,
)


def simple_surface() -> TerrainSurface:
    return TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=0.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )


def test_visible_terrain_triangle_projects() -> None:
    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 1
    assert projected.triangles[0].visible is True


def test_projected_triangle_preserves_elevations() -> None:
    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    triangle = projected.triangles[0]

    assert triangle.elevations_ft == (
        1000.0,
        1000.0,
        1300.0,
    )


def test_pitch_up_moves_terrain_down() -> None:
    computer = TerrainProjectionComputer()

    level = computer.project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    nose_up = computer.project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=10.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert (
        nose_up.triangles[0].first.y_px
        > level.triangles[0].first.y_px
    )


def test_triangle_behind_aircraft_is_hidden() -> None:
    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=180.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert projected.triangles[0].visible is False


def test_invalid_surface_fails_closed() -> None:
    projected = TerrainProjectionComputer().project(
        surface=TerrainSurface(
            valid=False,
            message="TERRAIN SAMPLE UNAVAILABLE",
        ),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is False
    assert projected.triangles == ()
    assert projected.message == (
        "TERRAIN SURFACE INVALID"
    )


def test_bad_triangle_index_fails_closed() -> None:
    surface = TerrainSurface(
        vertices=simple_surface().vertices,
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=99,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    projected = TerrainProjectionComputer().project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is False
    assert projected.triangles == ()
    assert projected.message == (
        "TERRAIN TRIANGLE INVALID"
    )
