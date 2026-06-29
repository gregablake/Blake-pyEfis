from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter


class EngineChecklistPage:
    def __init__(self) -> None:
        self.selected_index = 0
        self.checked: set[int] = set()

        self.items = [
            "MASTER - ON",
            "FUEL - CHECK QUANTITY",
            "FUEL VALVE - ON",
            "MIXTURE - RICH",
            "THROTTLE - CRACKED",
            "IGNITION A - ON",
            "IGNITION B - ON",
            "OIL PRESSURE - VERIFY AFTER START",
            "ALTERNATOR - ON",
            "CHT/EGT - MONITOR",
            "CANOPY/DOOR - LATCHED",
            "CONTROLS - FREE AND CORRECT",
        ]

    def move_selection(self, direction: int) -> None:
        self.selected_index = max(
            0,
            min(len(self.items) - 1, self.selected_index + direction),
        )

    def toggle_selected(self) -> None:
        if self.selected_index in self.checked:
            self.checked.remove(self.selected_index)
        else:
            self.checked.add(self.selected_index)

    def draw(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "ENGINE CHECKLIST",
        )

        y = 95
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        for index, item in enumerate(self.items):
            selected = index == self.selected_index
            checked = index in self.checked

            if selected:
                painter.fillRect(35, y - 25, width - 70, 34, QColor(40, 80, 40))

            painter.setPen(QColor(0, 255, 0) if checked else QColor(255, 255, 255))

            box = "[X]" if checked else "[ ]"
            cursor = ">" if selected else " "

            painter.drawText(55, y, f"{cursor} {box} {item}")
            y += 36

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(
            40,
            height - 40,
            "UP/DOWN = SELECT    SPACE/ENTER = CHECK    R = RESET    P = PFD    E = EMS"
        )
    def reset(self) -> None:
        self.selected_index = 0
        self.checked.clear()