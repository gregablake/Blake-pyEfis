from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter

from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.master_warning import get_engine_warnings
import csv
from pathlib import Path


@dataclass
class AlertRecord:
    timestamp_utc: str
    text: str
    color_name: str
    acknowledged: bool = False


class EmsAlertHistory:
    def __init__(self, max_alerts: int = 100) -> None:
        self.alerts: deque[AlertRecord] = deque(maxlen=max_alerts)
        self.active_alerts: set[str] = set()
        self.acknowledged_alerts: set[str] = set()
        self.silenced: bool = False
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_path = self.log_dir / "ems_alert_history.csv"

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
                    acknowledged=False,
                )
            )
        self.write_alert_to_csv(text)
        cleared_alerts = self.active_alerts - current

        for text in cleared_alerts:
            self.acknowledged_alerts.discard(text)

        self.active_alerts = current

    def acknowledge_active(self) -> None:
        self.acknowledged_alerts.update(self.active_alerts)

        for alert in self.alerts:
            if alert.text in self.active_alerts:
                alert.acknowledged = True

    def toggle_silence(self) -> None:
        self.silenced = not self.silenced

    def has_unacknowledged_active_alerts(self) -> bool:
        return bool(self.active_alerts - self.acknowledged_alerts)

    def write_alert_to_csv(self, text: str) -> None:
        file_exists = self.log_path.exists()

        with self.log_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["timestamp_utc", "alert"],
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "alert": text,
                }
            )

    def draw(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(255, 220, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "EMS ALERT HISTORY",
        )

        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            40,
            80,
            f"ACK: {len(self.acknowledged_alerts)}   SILENCED: {'YES' if self.silenced else 'NO'}",
        )

        painter.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        y = 120

        if not self.alerts:
            painter.setPen(QColor(0, 255, 0))
            painter.drawText(40, y, "No alerts recorded.")
        else:
            for alert in list(self.alerts)[:16]:
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(40, y, alert.timestamp_utc)

                painter.setPen(QColor(130, 130, 130) if alert.acknowledged else QColor(255, 220, 0))
                suffix = " ACK" if alert.acknowledged else ""
                painter.drawText(160, y, f"{alert.text}{suffix}")

                y += 30

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(
            40,
            height - 40,
            "A = ACKNOWLEDGE    S = SILENCE    E = EMS    T = TRENDS    P = PFD",
        )