from __future__ import annotations

from pyefis.user.blake_pfd.core.recommendation_display_stabilizer import (
    RecommendationDisplayStabilizer,
)
from pyefis.user.blake_pfd.master_warning import (
    draw_master_warning_strip,
)


class WarningManager:
    def __init__(self, app) -> None:
        self.app = app

        self.recommendation_stabilizer = (
            RecommendationDisplayStabilizer(
                activate_samples=3,
                clear_samples=5,
            )
        )

    def draw(
        self,
        painter,
        width: int,
    ) -> None:
        aircraft_moving = False

        if self.app.pfd is not None:
            aircraft_moving = (
                self.app.pfd.ground_speed_kt >= 35.0
            )

        display_recommendation = (
            self.recommendation_stabilizer.update(
                getattr(
                    self.app,
                    "aircraft_recommendation",
                    None,
                )
            )
        )

        draw_master_warning_strip(
            painter,
            self.app.engine_data,
            width,
            checklist=self.app.engine_checklist_page,
            aircraft_moving=aircraft_moving,
            aircraft_recommendation=display_recommendation,
        )