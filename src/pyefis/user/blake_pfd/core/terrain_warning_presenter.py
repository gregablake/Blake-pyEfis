from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TerrainWarningPresentation:
    visible: bool = False
    priority: str = "NONE"
    title: str = ""
    message: str = ""
    detail: str = ""
    flash: bool = False


class TerrainWarningPresenter:
    """
    Converts safely gated terrain and CFIT states into
    pilot-facing display content.

    Priority order:

    1. Valid CFIT collision prediction
    2. CRITICAL terrain alert
    3. WARNING terrain alert
    4. CAUTION terrain alert
    """

    def build(
        self,
        *,
        terrain_alert_state: Any,
        cfit_state: Any,
    ) -> TerrainWarningPresentation:
        cfit_prediction = getattr(
            cfit_state,
            "prediction",
            None,
        )

        cfit_valid = bool(
            getattr(
                cfit_state,
                "valid",
                False,
            )
        )

        collision_predicted = bool(
            getattr(
                cfit_prediction,
                "collision_predicted",
                False,
            )
        )

        if cfit_valid and collision_predicted:
            seconds = getattr(
                cfit_prediction,
                "seconds_to_collision",
                None,
            )

            distance_nm = getattr(
                cfit_prediction,
                "impact_distance_nm",
                None,
            )

            detail_parts: list[str] = []

            if seconds is not None:
                detail_parts.append(
                    f"IMPACT {max(0.0, float(seconds)):.0f} SEC"
                )

            if distance_nm is not None:
                detail_parts.append(
                    f"{max(0.0, float(distance_nm)):.1f} NM"
                )

            return TerrainWarningPresentation(
                visible=True,
                priority="CRITICAL",
                title="TERRAIN",
                message="PULL UP",
                detail="   ".join(detail_parts),
                flash=True,
            )

        alert_active = bool(
            getattr(
                terrain_alert_state,
                "active",
                False,
            )
        )

        if not alert_active:
            return TerrainWarningPresentation()

        warning_level = str(
            getattr(
                terrain_alert_state,
                "warning_level",
                "NONE",
            )
        ).strip().upper()

        alert_message = str(
            getattr(
                terrain_alert_state,
                "message",
                "",
            )
        ).strip()

        clearance = getattr(
            terrain_alert_state,
            "minimum_clearance_ft",
            None,
        )

        detail = ""

        if clearance is not None:
            detail = (
                f"PROJECTED CLEARANCE "
                f"{float(clearance):.0f} FT"
            )

        if warning_level == "CRITICAL":
            return TerrainWarningPresentation(
                visible=True,
                priority="CRITICAL",
                title="TERRAIN",
                message=(
                    alert_message
                    or "PULL UP"
                ),
                detail=detail,
                flash=True,
            )

        if warning_level == "WARNING":
            return TerrainWarningPresentation(
                visible=True,
                priority="WARNING",
                title="TERRAIN",
                message=(
                    alert_message
                    or "TERRAIN AHEAD"
                ),
                detail=detail,
                flash=False,
            )

        if warning_level == "CAUTION":
            return TerrainWarningPresentation(
                visible=True,
                priority="CAUTION",
                title="TERRAIN",
                message=(
                    alert_message
                    or "TERRAIN CLEARANCE LOW"
                ),
                detail=detail,
                flash=False,
            )

        return TerrainWarningPresentation()