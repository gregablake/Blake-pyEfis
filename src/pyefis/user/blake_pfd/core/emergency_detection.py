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
        sensor_status=None,
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

        explicit_running = getattr(
            engine_state,
            "running",
            None,
        )

        if explicit_running is not None:
            engine_running = bool(
                explicit_running
            )
        else:
            rpm_status_valid = (
                sensor_status is None
                or (
                    sensor_status.rpm.valid
                    and sensor_status.rpm.fresh
                )
            )

            engine_data = getattr(
                engine_state,
                "data",
                None,
            )

            rpm = (
                getattr(engine_data, "rpm", None)
                if engine_data is not None
                else None
            )

            engine_running = (
                True
                if (
                    not rpm_status_valid
                    or rpm is None
                )
                else float(rpm) > 0.0
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