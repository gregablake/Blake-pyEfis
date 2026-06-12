from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter


class AirportInfoPage:
    def draw(
        self,
        painter: QPainter,
        database,
        waypoint_id: str,
        width: int,
        height: int,
    ) -> None:
        airport = database.get_airport(waypoint_id)

        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "AIRPORT INFORMATION",
        )

        if airport is None:
            painter.setPen(QColor(255, 0, 0))
            painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            painter.drawText(40, 100, f"Airport not found: {waypoint_id}")
            return

        runway = database.best_runway(waypoint_id)
        freqs = database.get_frequencies(waypoint_id)

        y = 95

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(40, y, f"{airport.ident} - {airport.name}")
        y += 42

        painter.setFont(QFont("Arial", 15))
        painter.drawText(40, y, f"Elevation: {airport.elevation_ft:.0f} ft")
        y += 32
        painter.drawText(40, y, f"Lat/Lon: {airport.lat_deg:.5f}, {airport.lon_deg:.5f}")
        y += 45

        painter.setPen(QColor(0, 180, 255))
        painter.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        painter.drawText(40, y, "RUNWAY")
        y += 35

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 15))

        if runway:
            painter.drawText(60, y, f"RWY {runway.le_ident}/{runway.he_ident}")
            y += 30
            painter.drawText(
                60,
                y,
                f"{runway.length_ft:.0f} x {runway.width_ft:.0f} ft   {runway.surface}",
            )
            y += 30
            painter.drawText(
                60,
                y,
                f"Headings: {runway.le_heading_deg:.0f}° / {runway.he_heading_deg:.0f}°",
            )
            y += 45
        else:
            painter.drawText(60, y, "No runway data")
            y += 45

        painter.setPen(QColor(0, 180, 255))
        painter.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        painter.drawText(40, y, "FREQUENCIES")
        y += 35

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 14))

        if freqs:
            for freq in freqs[:10]:
                painter.drawText(
                    60,
                    y,
                    f"{freq.type:<8} {freq.frequency_mhz:.3f}  {freq.description}",
                )
                y += 26
        else:
            painter.drawText(60, y, "No frequency data")

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(40, height - 40, "F = FMS    P = PFD")