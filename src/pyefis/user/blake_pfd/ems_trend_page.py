from __future__ import annotations

from collections import deque

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen

from pyefis.user.blake_pfd.engine_data import EngineData


class EmsTrendPage:
    def __init__(self, max_samples: int = 300) -> None:
        self.samples: deque[EngineData] = deque(maxlen=max_samples)

    def add_sample(self, engine: EngineData) -> None:
        self.samples.append(engine)

    def draw(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "EMS TREND PAGE",
        )

        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(40, 90, f"Samples: {len(self.samples)}")

        self.draw_placeholder_chart(painter, 40, 130, width - 80, 180, "CHT TREND")
        self.draw_placeholder_chart(painter, 40, 340, width - 80, 180, "OIL / VOLTS TREND")

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(40, height - 40, "E = EMS    P = PFD")

    def draw_placeholder_chart(
        self,
        painter: QPainter,
        x: int,
        y: int,
        w: int,
        h: int,
        title: str,
    ) -> None:
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawRect(x, y, w, h)

        painter.setPen(QColor(0, 180, 255))
        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(x + 10, y + 25, title)