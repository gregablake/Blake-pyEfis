from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt
import json

class StratuxTrafficGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dbkey = "STRATUX_TRAFFIC_LIST"
        self.traffic = []
        self.setMinimumSize(80, 80)

    def setValue(self, value):
        try:
            self.traffic = json.loads(value)
        except Exception:
            self.traffic = []
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 10
        # Draw ownship
        qp.setBrush(QColor(Qt.GlobalColor.blue))
        qp.drawEllipse(cx-6, cy-6, 12, 12)
        # Draw traffic
        for t in self.traffic:
            brg = t.get("bearing", 0)
            dist = t.get("distance", 0)
            rel_alt = t.get("rel_alt", 0)
            # Scale: 2nm = r
            d = min(dist / 2.0, 1.0) * r
            angle_rad = (brg - 90) * 3.14159 / 180.0
            tx = cx + d * cos(angle_rad)
            ty = cy + d * sin(angle_rad)
            color = QColor(Qt.GlobalColor.red) if rel_alt and abs(rel_alt) < 500 else QColor(Qt.GlobalColor.yellow)
            qp.setBrush(color)
            qp.drawEllipse(int(tx)-4, int(ty)-4, 8, 8)
            # Optionally, draw relative altitude
            if rel_alt is not None:
                qp.setPen(Qt.GlobalColor.white)
                qp.drawText(int(tx)+6, int(ty), f"{int(rel_alt)}")

from math import cos, sin
