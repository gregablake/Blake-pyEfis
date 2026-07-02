from __future__ import annotations

from PyQt6.QtGui import QPainter


class PageRenderer:
    def __init__(self, app) -> None:
        self.app = app

    def _draw_page_with_warning_strip(self, draw_func, *args) -> None:
        painter = QPainter(self.app)
        draw_func(painter, *args)
        self.app.warning_manager.draw(painter, self.app.width())
        painter.end()

    def draw_page(self, painter: QPainter | None = None) -> bool:
        current_page = self.app.page_manager.current()

        if current_page == "FMS":
            if painter is not None:
                self.app.fms_page.draw(painter, self.app.route_manager, self.app.pfd, self.app.width(), self.app.height())
                self.app.warning_manager.draw(painter, self.app.width())
            else:
                self._draw_page_with_warning_strip(
                    self.app.fms_page.draw,
                    self.app.route_manager,
                    self.app.pfd,
                    self.app.width(),
                    self.app.height(),
                )
            return True

        if current_page == "AIRPORT":
            if painter is not None:
                self.app.airport_info_page.draw(painter, self.app.database, self.app.config.navigation.selected_waypoint_id, self.app.width(), self.app.height())
                self.app.warning_manager.draw(painter, self.app.width())
            else:
                self._draw_page_with_warning_strip(
                    self.app.airport_info_page.draw,
                    self.app.database,
                    self.app.config.navigation.selected_waypoint_id,
                    self.app.width(),
                    self.app.height(),
                )
            return True

        if current_page == "NEAREST":
            nearest = self.app.database.nearest_airports(
                39.1031,
                -84.5120,
                max_results=10,
            )
            if painter is not None:
                self.app.nearest_page.draw(painter, nearest, self.app.width(), self.app.height())
                self.app.warning_manager.draw(painter, self.app.width())
            else:
                self._draw_page_with_warning_strip(
                    self.app.nearest_page.draw,
                    nearest,
                    self.app.width(),
                    self.app.height(),
                )
            return True

        if current_page == "EMS":
            if painter is not None:
                self.app.ems_page.draw(
                    painter,
                    self.app.engine_data,
                    width,
                    height,
                    checklist=self.app.engine_checklist_page,
                    aircraft=self.app.aircraft,
                )
                self.app.warning_manager.draw(painter, self.app.width())
            else:
                self._draw_page_with_warning_strip(
                    self.app.ems_page.draw,
                    self.app.engine_data,
                    self.app.width(),
                    self.app.height(),
                    checklist=self.app.engine_checklist_page,
                )
            return True

        if current_page == "EMS_TREND":
            if painter is not None:
                self.app.ems_trend_page.draw(painter, self.app.width(), self.app.height())
                self.app.warning_manager.draw(painter, self.app.width())
            else:
                self._draw_page_with_warning_strip(
                    self.app.ems_trend_page.draw,
                    self.app.width(),
                    self.app.height(),
                )
            return True

        if current_page == "EMS_ALERTS":
            if painter is not None:
                self.app.ems_alert_history.draw(painter, self.app.width(), self.app.height())
                self.app.warning_manager.draw(painter, self.app.width())
            else:
                self._draw_page_with_warning_strip(
                    self.app.ems_alert_history.draw,
                    self.app.width(),
                    self.app.height(),
                )
            return True

        if current_page == "ENGINE_CHECKLIST":
            if painter is not None:
                self.app.engine_checklist_page.draw(painter, self.app.width(), self.app.height())
                self.app.warning_manager.draw(painter, self.app.width())
            else:
                self._draw_page_with_warning_strip(
                    self.app.engine_checklist_page.draw,
                    self.app.width(),
                    self.app.height(),
                )
            return True

        return False
