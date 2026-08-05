from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.cfit_predictor import (
    CfitPrediction,
    CfitPredictor,
)


@dataclass(frozen=True)
class CfitState:
    prediction: CfitPrediction = CfitPrediction()
    valid: bool = False


class CfitManager:

    def __init__(self) -> None:
        self.predictor = CfitPredictor()
        self.state = CfitState()

    def clear(self) -> None:
        self.state = CfitState()

    def update(
        self,
        *,
        aircraft_altitude_ft: float,
        vertical_speed_fpm: float,
        ground_speed_kt: float,
        terrain_profile,
    ) -> CfitState:

        prediction = self.predictor.predict(
            aircraft_altitude_ft=aircraft_altitude_ft,
            vertical_speed_fpm=vertical_speed_fpm,
            ground_speed_kt=ground_speed_kt,
            terrain_profile=terrain_profile,
        )

        self.state = CfitState(
            prediction=prediction,
            valid=True,
        )

        return self.state