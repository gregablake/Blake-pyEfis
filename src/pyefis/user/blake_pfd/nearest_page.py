from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter


class NearestPage:
    def __init__(self) -> None:
        self.selected_index = 0

    def move_selection(self, direction: int, airports: list) -> None:
        if not airports:
            self.selected_index = 0
            return

        self.selected_index = max(
            0,
            min(len(airports) - 1, self.selected_index + direction),
        )

    def selected_airport(self, airports: list):
        if not airports:
            return None

        return airports[self.selected_index]

    def draw(
        self,
        painter: QPainter,
        nearest_airports: list,
        width: int,
        height: int,
    ) -> None:

        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(255, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "NEAREST AIRPORTS",
        )

        y = 100

        painter.setFont(QFont("Arial", 16))

        for index, (distance_nm, airport) in enumerate(nearest_airports):

            selected = index == self.selected_index

            if selected:
                painter.fillRect(
                    40,
                    y - 24,
                    width - 80,
                    34,
                    QColor(70, 70, 20),
                )

            painter.setPen(
                QColor(255, 255, 0)
                if selected
                else QColor(255, 255, 255)
            )

            painter.drawText(
                60,
                y,
                f"{airport.ident:<6} "
                f"{distance_nm:5.1f} NM   "
                f"{airport.name}",
            )

            y += 40

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))

        painter.drawText(
            40,
            height - 40,
            "UP/DOWN = SELECT    ENTER = DIRECT-TO    P = PFD",
        )