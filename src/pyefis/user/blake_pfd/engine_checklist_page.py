from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter


class EngineChecklistPage:
    def __init__(self) -> None:
        self.selected_phase_index = 0
        self.selected_item_index = 0
        self.checked: dict[str, set[int]] = {}

        self.phases: list[tuple[str, list[str]]] = [
            (
                "BEFORE START",
                [
                    "MASTER - ON",
                    "FUEL QUANTITY - CHECK",
                    "FUEL VALVE - ON",
                    "MIXTURE - RICH",
                    "THROTTLE - CRACKED",
                    "IGNITION A - ON",
                    "IGNITION B - ON",
                    "EMS - VERIFY ONLINE",
                ],
            ),
            (
                "ENGINE START",
                [
                    "PROP AREA - CLEAR",
                    "STARTER - ENGAGE",
                    "RPM - STABILIZED",
                    "OIL PRESSURE - VERIFY",
                    "VOLTS - VERIFY",
                    "STARTER - DISENGAGED",
                ],
            ),
            (
                "RUNUP",
                [
                    "BRAKES - HOLD",
                    "RPM - SET RUNUP",
                    "IGNITION A - CHECK",
                    "IGNITION B - CHECK",
                    "OIL TEMP - GREEN",
                    "OIL PRESSURE - GREEN",
                    "CHT/EGT - CHECK",
                    "ALTERNATOR - VERIFY CHARGING",
                ],
            ),
            (
                "BEFORE TAKEOFF",
                [
                    "CONTROLS - FREE AND CORRECT",
                    "CANOPY/DOOR - LATCHED",
                    "TRIM - SET",
                    "FUEL VALVE - ON",
                    "IGNITION A - ON",
                    "IGNITION B - ON",
                    "EMS WARNINGS - NONE",
                    "TRANSPONDER/ADS-B - ON",
                ],
            ),
            (
                "CRUISE",
                [
                    "RPM - SET",
                    "FUEL FLOW - MONITOR",
                    "OIL TEMP/PRESS - MONITOR",
                    "CHT/EGT - MONITOR",
                    "VOLTS/AMPS - MONITOR",
                    "FUEL REMAINING - CHECK",
                ],
            ),
            (
                "LANDING",
                [
                    "FUEL - CHECK",
                    "MIXTURE - RICH",
                    "IGNITION A - ON",
                    "IGNITION B - ON",
                    "EMS - CHECK",
                    "SPEED - SET",
                    "RUNWAY - CONFIRMED",
                ],
            ),
        ]

    def current_phase_name(self) -> str:
        return self.phases[self.selected_phase_index][0]

    def current_items(self) -> list[str]:
        return self.phases[self.selected_phase_index][1]

    def current_checked(self) -> set[int]:
        phase = self.current_phase_name()
        self.checked.setdefault(phase, set())
        return self.checked[phase]

    def next_phase(self) -> None:
        self.selected_phase_index = min(
            len(self.phases) - 1,
            self.selected_phase_index + 1,
        )
        self.selected_item_index = 0

    def previous_phase(self) -> None:
        self.selected_phase_index = max(0, self.selected_phase_index - 1)
        self.selected_item_index = 0

    def move_selection(self, direction: int) -> None:
        items = self.current_items()

        self.selected_item_index = max(
            0,
            min(len(items) - 1, self.selected_item_index + direction),
        )

    def progress_summary(self) -> str:
        phase = self.current_phase_name()
        items = self.current_items()
        checked = self.current_checked()

        return f"{phase}: {len(checked)}/{len(items)}"

    def all_phases_summary(self) -> str:
        total_items = 0
        total_checked = 0

        for phase, items in self.phases:
            total_items += len(items)
            total_checked += len(self.checked.get(phase, set()))

        return f"TOTAL: {total_checked}/{total_items}"

    def toggle_selected(self) -> None:
        checked = self.current_checked()

        if self.selected_item_index in checked:
            checked.remove(self.selected_item_index)
        else:
            checked.add(self.selected_item_index)

    def reset_current_phase(self) -> None:
        self.current_checked().clear()
        self.selected_item_index = 0

    def reset_all(self) -> None:
        self.checked.clear()
        self.selected_phase_index = 0
        self.selected_item_index = 0

    def draw(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        phase_name = self.current_phase_name()
        items = self.current_items()
        checked = self.current_checked()

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "ENGINE CHECKLIST",
        )

        painter.setPen(QColor(0, 180, 255))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 70, width, 35),
            Qt.AlignmentFlag.AlignCenter,
            phase_name,
        )

        y = 125
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        for index, item in enumerate(items):
            selected = index == self.selected_item_index
            done = index in checked

            if selected:
                painter.fillRect(35, y - 25, width - 70, 34, QColor(40, 80, 40))

            painter.setPen(QColor(0, 255, 0) if done else QColor(255, 255, 255))

            box = "[X]" if done else "[ ]"
            cursor = ">" if selected else " "

            painter.drawText(55, y, f"{cursor} {box} {item}")
            y += 36

        complete_text = f"{len(checked)}/{len(items)} COMPLETE"
        painter.setPen(QColor(255, 220, 0))
        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(40, height - 70, complete_text)

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(
            40,
            height - 40,
            "LEFT/RIGHT = PHASE    UP/DOWN = ITEM    SPACE/ENTER = CHECK    R = RESET PHASE    SHIFT+R = RESET ALL",
        )
    def phase_complete(self, phase_name: str) -> bool:
        for phase, items in self.phases:
            if phase == phase_name:
                checked = self.checked.get(phase, set())
                return len(checked) == len(items)

        return False
    def set_phase_by_name(self, phase_name: str) -> None:
        phase_name = phase_name.upper()

        phase_map = {
            "PARKED": "BEFORE START",
            "RUNUP": "RUNUP",
            "TAXI": "BEFORE TAKEOFF",
            "TAKEOFF": "BEFORE TAKEOFF",
            "CLIMB": "CRUISE",
            "CRUISE": "CRUISE",
            "DESCENT": "LANDING",
            "LANDING": "LANDING",
        }

        checklist_name = phase_map.get(phase_name)

        if checklist_name is None:
            return

        for index, phase in enumerate(self.phases):
            if phase[0] == checklist_name:
                if self.selected_phase_index != index:
                    self.selected_phase_index = index
                    self.selected_item_index = 0
                return
            
    def active_phase_complete(self) -> bool:
        items = self.current_items()
        checked = self.current_checked()

        return len(checked) == len(items)