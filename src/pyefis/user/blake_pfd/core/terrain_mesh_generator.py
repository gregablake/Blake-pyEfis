from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TerrainVertex:
    x: float
    y: float
    elevation_ft: float


@dataclass(frozen=True)
class TerrainMesh:
    vertices: list[TerrainVertex]


class TerrainMeshGenerator:

    def generate(
        self,
        terrain_profile,
    ) -> TerrainMesh:

        vertices = []

        if not terrain_profile.points:
            return TerrainMesh(vertices=[])

        max_distance = max(
            p.distance_nm
            for p in terrain_profile.points
        )

        if max_distance <= 0:
            max_distance = 1.0

        for point in terrain_profile.points:

            x = (
                point.distance_nm
                / max_distance
            )

            vertices.append(
                TerrainVertex(
                    x=x,
                    y=0.0,
                    elevation_ft=point.elevation_ft,
                )
            )

        return TerrainMesh(vertices)