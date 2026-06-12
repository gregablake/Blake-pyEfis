from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter


class FmsPage:
    def draw(
        self,
        painter: QPainter,
        route_manager,
        flight_data,
        width: int,
        height: int,
    ) -> None:

        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "FLIGHT MANAGEMENT SYSTEM",
        )

        route = route_manager.load_route()

        painter.setFont(QFont("Arial", 16))

        y = 90

        painter.drawText(40, y, f"ROUTE: {route.get('route_id', 'NONE')}")
        y += 40

        waypoints = route.get("waypoints", [])

        active_leg = route_manager.get_active_leg()

        for wp in waypoints:
            marker = "  "

            if active_leg is not None:
                if wp == active_leg.to_ident:
                    marker = "► "

            painter.drawText(60, y, f"{marker}{wp}")
            y += 30

        y += 30

        painter.setFont(QFont("Arial", 14))

        if active_leg is not None:
            painter.drawText(
                40,
                y,
                f"ACTIVE: {active_leg.from_ident} → {active_leg.to_ident}",
            )
            y += 30

        painter.drawText(
            40,
            y,
            f"DTK: {flight_data.desired_track_deg:.0f}°",
        )
        y += 30

        painter.drawText(
            40,
            y,
            f"BRG: {flight_data.bearing_deg:.0f}°",
        )
        y += 30

        painter.drawText(
            40,
            y,
            f"DIS: {flight_data.distance_to_waypoint_nm:.1f} NM",
        )