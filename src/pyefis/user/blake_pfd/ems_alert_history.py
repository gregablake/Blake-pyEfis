from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter

from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.master_warning import get_engine_warnings


@dataclass
class AlertRecord:
    timestamp_utc: str
    text: str
    color_name: str


class EmsAlertHistory:
    def __init__(self, max_alerts: int = 100) -> None:
        self.alerts: deque[AlertRecord] = deque(maxlen=max_alerts)
        self.active_alerts: set[str] = set()

    def update(self, engine: EngineData) -> None:
        warnings = get_engine_warnings(engine)
        current = {warning.text for warning in warnings if warning.text != "ENGINE NORMAL"}

        new_alerts = current - self.active_alerts

        for text in sorted(new_alerts):
            self.alerts.appendleft(
                AlertRecord(
                    timestamp_utc=datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    text=text,
                    color_name="WARN",
                )
            )

        self.active_alerts = current

    def draw(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(255, 220, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "EMS ALERT HISTORY",
        )

        painter.setFont(QFont("Arial", 15, QFont.Weight.Bold))

        y = 95

        if not self.alerts:
            painter.setPen(QColor(0, 255, 0))
            painter.drawText(40, y, "No alerts recorded.")
        else:
            for alert in list(self.alerts)[:18]:
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(40, y, alert.timestamp_utc)

                painter.setPen(QColor(255, 220, 0))
                painter.drawText(160, y, alert.text)

                y += 30

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(40, height - 40, "E = EMS    T = TRENDS    P = PFD")