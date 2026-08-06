from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_mesh_generator import (
    TerrainMeshGenerator,
)


def profile():

    return SimpleNamespace(
        points=[
            SimpleNamespace(
                distance_nm=1,
                elevation_ft=800,
            ),
            SimpleNamespace(
                distance_nm=3,
                elevation_ft=1400,
            ),
            SimpleNamespace(
                distance_nm=5,
                elevation_ft=2100,
            ),
        ]
    )


def test_mesh():

    mesh = (
        TerrainMeshGenerator()
        .generate(profile())
    )

    assert len(mesh.vertices) == 3

    assert (
        mesh.vertices[2]
        .elevation_ft
        == 2100
    )


def test_empty():

    mesh = (
        TerrainMeshGenerator()
        .generate(
            SimpleNamespace(points=[])
        )
    )

    assert mesh.vertices == []