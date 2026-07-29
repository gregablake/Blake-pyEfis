from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TerrainCollisionPrediction:
    collision_predicted: bool
    clearance_ft: float
    message: str = ""


class TerrainCollisionPredictor:
    def evaluate(
        self,
        *,
        aircraft_altitude_ft: float,
        highest_terrain_ft: float,
        required_clearance_ft: float = 500.0,
    ) -> TerrainCollisionPrediction:

        clearance = (
            aircraft_altitude_ft
            - highest_terrain_ft
        )

        if clearance < required_clearance_ft:
            return TerrainCollisionPrediction(
                collision_predicted=True,
                clearance_ft=clearance,
                message="TERRAIN AHEAD",
            )

        return TerrainCollisionPrediction(
            collision_predicted=False,
            clearance_ft=clearance,
        )