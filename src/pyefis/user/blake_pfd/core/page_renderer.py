from __future__ import annotations

from PyQt6.QtGui import QPainter


class PageRenderer:
    def __init__(self, app) -> None:
        self.app = app

    def draw(self, painter: QPainter, width: int, height: int) -> bool:
        current_page = self.app.page_manager.current()

        if current_page == "FMS":
            self.app.fms_page.draw(
                painter,
                self.app.route_manager,
                self.app.pfd,
                width,
                height,
            )
            self.app.draw_warning_strip(painter, width)
            return True

        if current_page == "AIRPORT":
            self.app.airport_info_page.draw(
                painter,
                self.app.database,
                self.app.config.navigation.selected_waypoint_id,
                width,
                height,
            )
            self.app.draw_warning_strip(painter, width)
            return True

        if current_page == "NEAREST":
            nearest = self.app.database.nearest_airports(
                39.1031,
                -84.5120,
                max_results=10,
            )

            self.app.nearest_page.draw(
                painter,
                nearest,
                width,
                height,
            )
            self.app.draw_warning_strip(painter, width)
            return True

        if current_page == "EMS":
            self.app.ems_page.draw(
                painter,
                self.app.aircraft,
                width,
                height,
                checklist=self.app.engine_checklist_page,
                aircraft_recommendation=self.app.aircraft_recommendation,
            )   
            self.app.draw_warning_strip(painter, width)
            return True

        if current_page == "EMS_TREND":
            self.app.ems_trend_page.draw(
                painter,
                width,
                height,
            )
            self.app.draw_warning_strip(painter, width)
            return True

        if current_page == "EMS_ALERTS":
            self.app.ems_alert_history.draw(
                painter,
                width,
                height,
            )
            self.app.draw_warning_strip(painter, width)
            return True

        if current_page == "ENGINE_CHECKLIST":
            self.app.engine_checklist_page.draw(
                painter,
                width,
                height,
            )
            self.app.draw_warning_strip(painter, width)
            return True

        return False