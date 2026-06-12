from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter


class FmsPage:
    def __init__(self) -> None:
        self.selected_index = 0

    def move_selection(self, direction: int, route_manager) -> None:
        route = route_manager.load_route()
        waypoints = route.get("waypoints", [])

        if not waypoints:
            self.selected_index = 0
            return

        self.selected_index = max(
            0,
            min(len(waypoints) - 1, self.selected_index + direction),
        )

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
        active_leg = route_manager.get_active_leg()
        waypoints = route.get("waypoints", [])

        painter.setFont(QFont("Arial", 16))
        y = 90

        painter.drawText(40, y, f"ROUTE: {route.get('route_id', 'NONE')}")
        y += 45

        for index, wp in enumerate(waypoints):
            selected = index == self.selected_index
            active = active_leg is not None and wp == active_leg.to_ident

            if selected:
                painter.fillRect(45, y - 22, 220, 30, QColor(40, 80, 40))

            marker = "►" if active else " "
            cursor = ">" if selected else " "

            painter.setPen(QColor(255, 255, 0) if selected else QColor(255, 255, 255))
            painter.drawText(60, y, f"{cursor} {marker} {wp}")

            y += 34

        y += 25
        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 14))

        if active_leg is not None:
            painter.drawText(40, y, f"ACTIVE: {active_leg.from_ident} → {active_leg.to_ident}")
            y += 30

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(40, y, f"DTK: {flight_data.desired_track_deg:.0f}°")
        y += 30
        painter.drawText(40, y, f"BRG: {flight_data.bearing_deg:.0f}°")
        y += 30
        painter.drawText(40, y, f"DIS: {flight_data.distance_to_waypoint_nm:.1f} NM")

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(40, height - 40, "UP/DOWN = select    P = PFD")