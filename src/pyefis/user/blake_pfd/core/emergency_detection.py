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


class EmergencyDetection:
    def evaluate(
        self,
        *,
        engine_state: EngineState | None,
        flight_state: FlightState | None,
    ) -> EmergencyStatus:

        if engine_state is None:
            return EmergencyStatus()

        if flight_state is None:
            return EmergencyStatus()

        if (
            flight_state.phase.upper()
            in {
                "TAKEOFF",
                "CLIMB",
                "CRUISE",
                "DESCENT",
            }
            and engine_state.running is False
        ):
            return EmergencyStatus(
                active=True,
                reason="ENGINE_STOPPED",
            )

        return EmergencyStatus()