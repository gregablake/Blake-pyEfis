from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.engine_state import (
    EngineState,
)
from pyefis.user.blake_pfd.core.flight_state_manager import (
    FlightState,
)


@dataclass(frozen=True)
class EmergencyStatus:
    active: bool = False
    reason: str = ""
    automatic: bool = False
    pilot_selected: bool = False


class EmergencyDetection:
    def evaluate(
        self,
        *,
        engine_state: EngineState | None,
        flight_state: FlightState | None,
        pilot_selected: bool = False,
    ) -> EmergencyStatus:
        if pilot_selected:
            return EmergencyStatus(
                active=True,
                reason="PILOT_SELECTED",
                automatic=False,
                pilot_selected=True,
            )

        if engine_state is None:
            return EmergencyStatus()

        if flight_state is None:
            return EmergencyStatus()

        phase = str(
            getattr(
                flight_state,
                "phase",
                "UNKNOWN",
            )
        ).upper()

        engine_running = bool(
            getattr(
                engine_state,
                "running",
                True,
            )
        )

        if (
            phase
            in {
                "TAKEOFF",
                "CLIMB",
                "CRUISE",
                "DESCENT",
            }
            and not engine_running
        ):
            return EmergencyStatus(
                active=True,
                reason="ENGINE_STOPPED",
                automatic=True,
                pilot_selected=False,
            )

        return EmergencyStatus()