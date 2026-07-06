from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChecklistState:
    active: str = "NONE"


class ChecklistManager:
    def __init__(self) -> None:
        self.state = ChecklistState()

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

        self.state.active = table.get(phase, "Checklist")

        return self.state