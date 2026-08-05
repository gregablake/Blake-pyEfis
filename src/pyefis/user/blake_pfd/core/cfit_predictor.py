from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CfitPrediction:
    collision_predicted: bool = False
    seconds_to_collision: float | None = None
    impact_distance_nm: float | None = None
    terrain_clearance_ft: float | None = None
    message: str = ""


class CfitPredictor:

    LOOKAHEAD_SECONDS = (
        30,
        45,
        60,
        90,
    )

    def predict(
        self,
        *,
        aircraft_altitude_ft: float,
        vertical_speed_fpm: float,
        ground_speed_kt: float,
        terrain_profile,
    ) -> CfitPrediction:

        if not terrain_profile.points:
            return CfitPrediction()

        for point in terrain_profile.points:

            if ground_speed_kt <= 1:
                continue

            seconds = (
                point.distance_nm
                / ground_speed_kt
            ) * 3600.0

            predicted_altitude = (
                aircraft_altitude_ft
                +
                (
                    vertical_speed_fpm
                    / 60.0
                )
                * seconds
            )

            clearance = (
                predicted_altitude
                - point.elevation_ft
            )

            if clearance <= 0:

                return CfitPrediction(
                    collision_predicted=True,
                    seconds_to_collision=seconds,
                    impact_distance_nm=(
                        point.distance_nm
                    ),
                    terrain_clearance_ft=clearance,
                    message="CFIT PREDICTED",
                )

        return CfitPrediction(
            collision_predicted=False,
            terrain_clearance_ft=(
                aircraft_altitude_ft
                -
                max(
                    p.elevation_ft
                    for p in terrain_profile.points
                )
            ),
        )