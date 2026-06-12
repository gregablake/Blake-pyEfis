from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter

from pyefis.user.blake_pfd.engine_data import EngineData


class EmsPage:
    def draw(
        self,
        painter: QPainter,
        engine: EngineData,
        width: int,
        height: int,
    ) -> None:

        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "ENGINE MONITORING SYSTEM",
        )
        self.draw_annunciators(
            painter,
            engine,
            width,
        )

        y = 90

        painter.setFont(QFont("Arial", 16))
        painter.setPen(QColor(255, 255, 255))

        painter.drawText(40, y, f"RPM:            {engine.rpm:.0f}")
        y += 35

        painter.drawText(40, y, f"VOLTS:          {engine.volts:.1f}")
        y += 35

        painter.drawText(40, y, f"AMPS:           {engine.amps:+.1f}")
        y += 35

        painter.drawText(40, y, f"OIL PSI:        {engine.oil_pressure_psi:.0f}")
        y += 35

        painter.drawText(40, y, f"OIL TEMP:       {engine.oil_temp_f:.0f}°F")
        y += 35

        painter.drawText(40, y, f"FUEL PSI:       {engine.fuel_pressure_psi:.1f}")
        y += 50

        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        for i, cht in enumerate(engine.cht_f):
            painter.setPen(self.temperature_color(cht, 425, 450))
            painter.drawText(
                40,
                y,
                f"CHT{i+1}: {cht:.0f}°F",
            )
            y += 28

        y = 300

        for i, egt in enumerate(engine.egt_f):
            painter.setPen(self.temperature_color(egt, 1450, 1500))
            painter.drawText(
                350,
                y,
                f"EGT{i+1}: {egt:.0f}°F",
            )
            y += 35

        y = height - 120

        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        painter.setPen(QColor(0, 255, 0) if engine.ignition_a else QColor(255, 0, 0))
        painter.drawText(40, y, f"IGN A {'ON' if engine.ignition_a else 'OFF'}")

        y += 30

        painter.setPen(QColor(0, 255, 0) if engine.ignition_b else QColor(255, 0, 0))
        painter.drawText(40, y, f"IGN B {'ON' if engine.ignition_b else 'OFF'}")

        y += 30

        painter.setPen(QColor(0, 255, 0) if engine.alternator_online else QColor(255, 0, 0))
        painter.drawText(40, y, f"ALT {'ON' if engine.alternator_online else 'OFF'}")

        y += 30

        painter.setPen(QColor(255, 220, 0) if engine.starter_engaged else QColor(255, 255, 255))
        painter.drawText(40, y, f"START {'ON' if engine.starter_engaged else 'OFF'}")

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))

        painter.drawText(
            40,
            height - 20,
            "P = PFD    E = EMS",
        )
        
    def draw_annunciators(
        self,
        painter: QPainter,
        engine: EngineData,
        width: int,
    ) -> None:

        annunciators = []

        if engine.rpm > 1700 and engine.oil_pressure_psi < 16:
            annunciators.append(("LOW OIL PRESS", QColor(255, 0, 0)))

        if engine.oil_temp_f > 260:
            annunciators.append(("HIGH OIL TEMP", QColor(255, 0, 0)))
        elif engine.oil_temp_f > 235:
            annunciators.append(("OIL TEMP", QColor(255, 220, 0)))

        if engine.volts < 12.0:
            annunciators.append(("LOW VOLTS", QColor(255, 0, 0)))
        elif engine.volts < 12.5:
            annunciators.append(("VOLTS", QColor(255, 220, 0)))

        if not engine.alternator_online:
            annunciators.append(("ALT FAIL", QColor(255, 0, 0)))

        if not engine.ignition_a:
            annunciators.append(("IGN A", QColor(255, 0, 0)))

        if not engine.ignition_b:
            annunciators.append(("IGN B", QColor(255, 0, 0)))

        if engine.starter_engaged:
            annunciators.append(("START", QColor(255, 220, 0)))

        if not annunciators:
            annunciators.append(("ENGINE NORMAL", QColor(0, 255, 0)))

        x = 20

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        for text, color in annunciators:
            painter.fillRect(x, 55, 140, 28, color)

            painter.setPen(QColor(0, 0, 0))
            painter.drawText(
                QRectF(x, 55, 140, 28),
                Qt.AlignmentFlag.AlignCenter,
                text,
            )

            x += 150

    def temperature_color(
        self,
        value: float,
        yellow_limit: float,
        red_limit: float,
    ) -> QColor:

        if value >= red_limit:
            return QColor(255, 0, 0)

        if value >= yellow_limit:
            return QColor(255, 220, 0)

        return QColor(0, 255, 0)