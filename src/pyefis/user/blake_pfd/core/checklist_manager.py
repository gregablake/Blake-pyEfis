from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChecklistState:
    active: str = "NONE"
    should_popup: bool = False


class ChecklistManager:
    def __init__(self) -> None:
        self.state = ChecklistState()
        self.last_popup_phase: str | None = None

    def update(self, phase: str) -> ChecklistState:
        table = {
            "PARKED": "Preflight",
            "RUNUP": "Runup",
            "TAKEOFF": "Before Takeoff",
            "CLIMB": "After Takeoff",
            "CRUISE": "Cruise",
            "DESCENT": "Descent",
            "LANDING": "Before Landing",
        }

        popup_phases = {
            "RUNUP",
            "TAKEOFF",
            "DESCENT",
            "LANDING",
        }

        active = table.get(phase, "Checklist")
        should_popup = phase in popup_phases and phase != self.last_popup_phase

        if should_popup:
            self.last_popup_phase = phase

        self.state = ChecklistState(
            active=active,
            should_popup=should_popup,
        )

        return self.state