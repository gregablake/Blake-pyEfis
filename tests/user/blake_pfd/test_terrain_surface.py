from __future__ import annotations

from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurfaceGenerator,
)


FEET_PER_NM = 6076.12


def generator(
    elevation_sampler,
) -> TerrainSurfaceGenerator:
    return TerrainSurfaceGenerator(
        elevation_sampler=elevation_sampler,
        forward_distances_nm=(
            1.0,
            2.0,
            3.0,
        ),
        lateral_fractions=(
            -1.0,
            0.0,
            1.0,
        ),
        half_width_ratio=0.5,
    )


def test_surface_builds_two_dimensional_grid() -> None:
    surface = generator(
        lambda latitude, longitude: 1000.0
    ).generate(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1500.0,
        heading_deg=0.0,
    )

    assert surface.valid is True
    assert surface.rows == 3
    assert surface.columns == 3
    assert len(surface.vertices) == 9
    assert len(surface.triangles) == 8


def test_heading_north_places_left_and_right_correctly() -> None:
    surface = generator(
        lambda latitude, longitude: 1000.0
    ).generate(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1500.0,
        heading_deg=0.0,
    )

    assert surface.valid is True

    left = surface.vertices[0]
    center = surface.vertices[1]
    right = surface.vertices[2]

    assert left.east_ft < 0.0
    assert right.east_ft > 0.0

    assert abs(center.east_ft) < 1e-6
    assert abs(
        center.north_ft - FEET_PER_NM
    ) < 1e-6


def test_heading_east_rotates_surface_with_aircraft() -> None:
    surface = generator(
        lambda latitude, longitude: 1000.0
    ).generate(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1500.0,
        heading_deg=90.0,
    )

    assert surface.valid is True

    center = surface.vertices[1]

    assert abs(center.north_ft) < 1e-6
    assert abs(
        center.east_ft - FEET_PER_NM
    ) < 1e-6


def test_surface_vertical_coordinate_is_aircraft_relative() -> None:
    surface = generator(
        lambda latitude, longitude: 800.0
    ).generate(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1500.0,
        heading_deg=0.0,
    )

    assert surface.valid is True

    for vertex in surface.vertices:
        assert vertex.elevation_ft == 800.0
        assert vertex.up_ft == -700.0


def test_missing_terrain_sample_fails_closed() -> None:
    surface = generator(
        lambda latitude, longitude: None
    ).generate(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1500.0,
        heading_deg=0.0,
    )

    assert surface.valid is False
    assert surface.vertices == ()
    assert surface.triangles == ()
    assert surface.message == (
        "TERRAIN SAMPLE UNAVAILABLE"
    )


def test_invalid_aircraft_position_fails_closed() -> None:
    surface = generator(
        lambda latitude, longitude: 1000.0
    ).generate(
        aircraft_lat_deg=200.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1500.0,
        heading_deg=0.0,
    )

    assert surface.valid is False
    assert surface.vertices == ()
    assert surface.triangles == ()
    assert surface.message == (
        "AIRCRAFT POSITION INVALID"
    )
