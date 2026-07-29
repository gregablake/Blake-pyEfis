from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LandingSiteStatus:
    airport_reachable: bool
    warning: str = ""


class LandingSiteMonitor:
    def evaluate(
        self,
        *,
        selected_airport_distance_nm: float | None,
        max_glide_distance_nm: float,
    ) -> LandingSiteStatus:

        if selected_airport_distance_nm is None:
            return LandingSiteStatus(
                airport_reachable=False,
                warning="NO_AIRPORT_SELECTED",
            )

        if selected_airport_distance_nm <= max_glide_distance_nm:
            return LandingSiteStatus(
                airport_reachable=True,
            )

        return LandingSiteStatus(
            airport_reachable=False,
            warning="AIRPORT_OUT_OF_GLIDE_RANGE",
        )