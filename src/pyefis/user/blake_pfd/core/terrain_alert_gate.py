from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TerrainAlertState:
    active: bool = False
    warning_level: str = "NONE"
    message: str = ""
    minimum_clearance_ft: float | None = None
    predictive_alerts_enabled: bool = False
    suppressed_reason: str = ""


class TerrainAlertGate:
    """
    Allows terrain alerts only when:

    1. Predictive terrain alerts are enabled.
    2. Real terrain data is active.
    3. The terrain-awareness result is valid.
    4. The awareness warning level is actionable.
    """

    ACTIONABLE_LEVELS = {
        "CAUTION",
        "WARNING",
        "CRITICAL",
    }

    def evaluate(
        self,
        *,
        startup_status: Any,
        terrain_awareness_state: Any,
        real_terrain_enabled: bool,
    ) -> TerrainAlertState:
        predictive_enabled = bool(
            getattr(
                startup_status,
                "predictive_alerts_enabled",
                False,
            )
        )

        if not real_terrain_enabled:
            return TerrainAlertState(
                predictive_alerts_enabled=False,
                suppressed_reason=(
                    "REAL TERRAIN DATA NOT ENABLED"
                ),
            )

        if not predictive_enabled:
            return TerrainAlertState(
                predictive_alerts_enabled=False,
                suppressed_reason=(
                    getattr(
                        startup_status,
                        "message",
                        "",
                    )
                    or "PREDICTIVE TERRAIN ALERTS DISABLED"
                ),
            )

        manager_valid = bool(
            getattr(
                terrain_awareness_state,
                "valid",
                False,
            )
        )

        if not manager_valid:
            return TerrainAlertState(
                predictive_alerts_enabled=True,
                suppressed_reason=(
                    getattr(
                        terrain_awareness_state,
                        "message",
                        "",
                    )
                    or "TERRAIN AWARENESS DATA INVALID"
                ),
            )

        awareness = getattr(
            terrain_awareness_state,
            "awareness",
            None,
        )

        if awareness is None:
            return TerrainAlertState(
                predictive_alerts_enabled=True,
                suppressed_reason=(
                    "TERRAIN AWARENESS RESULT MISSING"
                ),
            )

        awareness_valid = bool(
            getattr(
                awareness,
                "valid",
                False,
            )
        )

        if not awareness_valid:
            return TerrainAlertState(
                predictive_alerts_enabled=True,
                suppressed_reason=(
                    getattr(
                        awareness,
                        "message",
                        "",
                    )
                    or "TERRAIN AWARENESS RESULT INVALID"
                ),
            )

        warning_level = str(
            getattr(
                awareness,
                "warning_level",
                "NONE",
            )
        ).strip().upper()

        message = str(
            getattr(
                awareness,
                "message",
                "",
            )
        ).strip()

        minimum_clearance_ft = getattr(
            awareness,
            "minimum_clearance_ft",
            None,
        )

        if warning_level not in self.ACTIONABLE_LEVELS:
            return TerrainAlertState(
                predictive_alerts_enabled=True,
                warning_level="NONE",
                minimum_clearance_ft=(
                    minimum_clearance_ft
                ),
            )

        return TerrainAlertState(
            active=True,
            warning_level=warning_level,
            message=message,
            minimum_clearance_ft=(
                minimum_clearance_ft
            ),
            predictive_alerts_enabled=True,
        )