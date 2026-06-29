from __future__ import annotations

import argparse
import sys
from math import cos, radians, sin

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF
from PyQt6.QtWidgets import QApplication, QWidget

from pyefis.user.blake_pfd.airport_info_page import AirportInfoPage
from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.database_importer import AviationDatabase
from pyefis.user.blake_pfd.ems_page import EmsPage
from pyefis.user.blake_pfd.engine_sim import SimulatedEngineSource
from pyefis.user.blake_pfd.flight_computer import FlightComputer, FlightData
from pyefis.user.blake_pfd.flight_logger import FlightLogger
from pyefis.user.blake_pfd.fms_page import FmsPage
from pyefis.user.blake_pfd.hardware_readers import BlakeHardwareSensorSource
from pyefis.user.blake_pfd.log_replay import LogReplaySource
from pyefis.user.blake_pfd.master_warning import draw_master_warning_strip
from pyefis.user.blake_pfd.moving_map import MovingMapComputer
from pyefis.user.blake_pfd.nearest_page import NearestPage
from pyefis.user.blake_pfd.obstacles import ObstacleComputer
from pyefis.user.blake_pfd.route_manager import RouteManager
from pyefis.user.blake_pfd.safe_taxi import SafeTaxiComputer
from pyefis.user.blake_pfd.sensors_sim import SimulatedSensorSource
from pyefis.user.blake_pfd.startup_check import run_startup_check
from pyefis.user.blake_pfd.stratux_reader import StratuxReader
from pyefis.user.blake_pfd.synthetic_vision import (
    SyntheticVisionComputer,
    project_object_to_screen,
)
from pyefis.user.blake_pfd.terrain import TerrainComputer
from pyefis.user.blake_pfd.weather_reader import WeatherReader
from pyefis.user.blake_pfd.ems_trend_page import EmsTrendPage
from pyefis.user.blake_pfd.ems_alert_history import EmsAlertHistory
from pathlib import Path
import yaml
from pyefis.user.blake_pfd.audio_alerts import AudioAlertManager


class BlakePfdDemo(QWidget):
    def __init__(self, use_hardware: bool = False, replay_log: str | None = None) -> None:
        super().__init__()

        self.config = load_config()
        self.startup_status = run_startup_check()
        self.database = AviationDatabase()
        self.database.load_all()
        self.route_manager = RouteManager()
        self.flight_computer = FlightComputer()
        self.synthetic_vision = SyntheticVisionComputer()
        self.safe_taxi = SafeTaxiComputer()
        self.moving_map = MovingMapComputer()
        self.terrain = TerrainComputer()
        self.obstacles = ObstacleComputer()
        self.weather = WeatherReader()
        self.fms_page = FmsPage()
        self.airport_info_page = AirportInfoPage()
        self.nearest_page = NearestPage()
        self.ems_page = EmsPage()
        self.ems_trend_page = EmsTrendPage()
        self.ems_alert_history = EmsAlertHistory()

        self.engine_source = SimulatedEngineSource()
        self.engine_data = self.engine_source.read()

        self.flight_logger = FlightLogger(
            log_interval_s=self.config.logging.interval_s,
        )

        self.stratux = StratuxReader(
            host=self.config.stratux.host,
            port=self.config.stratux.gdl90_port,
        )

        self.replay_source = LogReplaySource(replay_log) if replay_log else None
        self.sensors = BlakeHardwareSensorSource() if use_hardware else SimulatedSensorSource()
        self.use_hardware = use_hardware
        self.pfd: FlightData | None = None
        self.current_page = "PFD"

        mode_name = "Replay" if replay_log else ("Hardware" if use_hardware else "Simulator")
        self.setWindowTitle(f"Blake PFD Demo - {mode_name}")
        self.resize(self.config.display.width, self.config.display.height)

        if self.config.display.fullscreen:
            self.showFullScreen()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)
        self.audio_alerts = AudioAlertManager()

    def update_data(self) -> None:
        if self.replay_source is not None:
            self.pfd = self.replay_source.read()
        else:
            raw = self.sensors.read()
            self.pfd = self.flight_computer.update(raw)

        self.engine_data = self.engine_source.read()
        self.ems_alert_history.update(self.engine_data)
        self.audio_alerts.update(
            self.engine_data,
            silenced=self.ems_alert_history.silenced,
)
        self.ems_trend_page.add_sample(self.engine_data)

        if self.config.logging.enabled and self.pfd is not None:
            self.flight_logger.maybe_log(
                self.pfd,
                waypoint_id=self.config.navigation.selected_waypoint_id,
                engine=self.engine_data,
            )

        self.update()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()

        if self.current_page == "EMS_ALERTS":
            if key == Qt.Key.Key_A:
                self.ems_alert_history.acknowledge_active()
                self.update()
                return

            if key == Qt.Key.Key_S:
                self.ems_alert_history.toggle_silence()
                self.update()
                return

        if key == Qt.Key.Key_P:
            self.current_page = "PFD"

        elif key == Qt.Key.Key_F:
            self.current_page = "FMS"

        elif key == Qt.Key.Key_A:
            self.current_page = "AIRPORT"

        elif key == Qt.Key.Key_N:
            self.current_page = "NEAREST"

        elif key == Qt.Key.Key_E:
            self.current_page = "EMS"

        elif key == Qt.Key.Key_T:
            self.current_page = "EMS_TREND"

        elif key == Qt.Key.Key_H:
            self.current_page = "EMS_ALERTS"

        elif self.current_page == "FMS":
            if key == Qt.Key.Key_Up:
                self.fms_page.move_selection(-1, self.route_manager)

            elif key == Qt.Key.Key_Down:
                self.fms_page.move_selection(1, self.route_manager)

            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                selected = self.fms_page.get_selected_waypoint(self.route_manager)
                if selected is not None:
                    self.activate_direct_to(selected)

        elif self.current_page == "NEAREST":
            nearest = self.database.nearest_airports(
                39.1031,
                -84.5120,
                max_results=10,
            )

            if key == Qt.Key.Key_Up:
                self.nearest_page.move_selection(-1, nearest)

            elif key == Qt.Key.Key_Down:
                self.nearest_page.move_selection(1, nearest)

            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                selection = self.nearest_page.selected_airport(nearest)

                if selection is not None:
                    _distance_nm, airport = selection
                    self.activate_direct_to(airport.ident)
            elif event.key() == Qt.Key.Key_X:
                self.cycle_ems_test_mode()

        self.update()

    def activate_direct_to(self, waypoint_id: str) -> None:
        waypoint_id = waypoint_id.upper()
        print(f"Activating Direct-To {waypoint_id}")

        self.config.navigation.selected_waypoint_id = waypoint_id
        self.flight_computer.config.navigation.selected_waypoint_id = waypoint_id

    def cycle_ems_test_mode(self) -> None:
        modes = [
            "normal",
            "high_cht",
            "high_egt",
            "low_oil",
            "alt_fail",
            "ign_fail",
            "low_fuel",
        ]

        current = getattr(self.config.ems_test, "mode", "normal")

        try:
            index = modes.index(current)
        except ValueError:
            index = 0

        next_mode = modes[(index + 1) % len(modes)]

        config_path = Path(__file__).with_name("pfd_config.yaml")
        raw = yaml.safe_load(config_path.read_text()) or {}

        raw.setdefault("ems_test", {})
        raw["ems_test"]["mode"] = next_mode

        config_path.write_text(yaml.safe_dump(raw, sort_keys=False))

        self.config = load_config()
        self.flight_computer.config = self.config

        print(f"EMS test mode: {next_mode}")

    def paintEvent(self, event) -> None:  # noqa: N802
        if self.pfd is None:
            return

        if self.current_page == "FMS":
            painter = QPainter(self)
            self.fms_page.draw(
                painter,
                self.route_manager,
                self.pfd,
                self.width(),
                self.height(),
            )
            draw_master_warning_strip(painter, self.engine_data, self.width())
            painter.end()
            return

        if self.current_page == "AIRPORT":
            painter = QPainter(self)
            self.airport_info_page.draw(
                painter,
                self.database,
                self.config.navigation.selected_waypoint_id,
                self.width(),
                self.height(),
            )
            draw_master_warning_strip(painter, self.engine_data, self.width())
            painter.end()
            return

        if self.current_page == "NEAREST":
            nearest = self.database.nearest_airports(
                39.1031,
                -84.5120,
                max_results=10,
            )

            painter = QPainter(self)
            self.nearest_page.draw(
                painter,
                nearest,
                self.width(),
                self.height(),
            )
            draw_master_warning_strip(painter, self.engine_data, self.width())
            painter.end()
            return

        if self.current_page == "EMS":
            painter = QPainter(self)
            self.ems_page.draw(
                painter,
                self.engine_data,
                self.width(),
                self.height(),
            )
            draw_master_warning_strip(painter, self.engine_data, self.width())
            painter.end()
            return
        
        if self.current_page == "EMS_ALERTS":
            painter = QPainter(self)
            self.ems_alert_history.draw(
                painter,
                self.width(),
                self.height(),
            )
            draw_master_warning_strip(painter, self.engine_data, self.width())
            painter.end()
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        features = self.config.features
        declutter_level = self.config.declutter.level

        self.draw_background(painter, width, height)

        taxi_state = self.safe_taxi.update(self.pfd)
        if features.show_safe_taxi and taxi_state.active:
            self.draw_safe_taxi_map(painter, taxi_state, width, height)
            draw_master_warning_strip(painter, self.engine_data, width)
            painter.end()
            return

        if features.show_synthetic_vision:
            self.draw_synthetic_vision(painter, self.pfd, width, height)

        if features.show_attitude:
            self.draw_attitude(painter, self.pfd, width, height)

        if features.show_airspeed:
            self.draw_airspeed_tape(painter, self.pfd, width, height)

        if features.show_altitude:
            self.draw_altitude_tape(painter, self.pfd, width, height)

        if features.show_vsi:
            self.draw_vsi(painter, self.pfd, width, height)

        if features.show_heading or features.show_hsi:
            self.draw_heading_strip(painter, self.pfd, width, height)

        if features.show_hsi:
            self.draw_hsi_compass_rose(painter, self.pfd, width, height)

        if features.show_turn_rate or features.show_slip_skid:
            self.draw_turn_and_slip(painter, self.pfd, width, height)

        if features.show_cdi or (features.show_vdi and self.config.vnav.enabled):
            self.draw_nav_cdi_vdi(painter, self.pfd, width, height)

        self.draw_top_data_bar(painter, self.pfd, width)
        self.draw_bottom_data_bar(painter, self.pfd, width, height)

        if declutter_level <= 0 and features.show_nearest_airports:
            self.draw_nearest_airports_overlay(painter, self.pfd, width, height)

        if declutter_level <= 0 and features.show_moving_map:
            map_state = self.moving_map.update(
                database=self.database,
                aircraft_lat=39.1031,
                aircraft_lon=-84.5120,
                range_nm=self.config.moving_map.range_nm,
            )
            self.draw_moving_map_overlay(painter, map_state, width, height)

        if declutter_level <= 0 and features.show_route:
            self.draw_route_overlay(painter, width, height)

        if declutter_level <= 0 and features.show_airport_info:
            self.draw_selected_airport_info(painter, width, height)

        if declutter_level <= 0:
            self.draw_waypoint_info_box(painter, self.pfd, width, height)
            self.draw_startup_status_box(painter, width, height)
            self.draw_sensor_status_panel(painter, width, height)
            self.draw_sim_profile_box(painter, width, height)

        if declutter_level <= 1:
            self.draw_navigation_status_box(painter, self.pfd, width, height)

        if declutter_level <= 1 and self.config.vnav.enabled:
            self.draw_vnav_info_box(painter, self.pfd, width, height)

        if features.show_terrain:
            terrain_state = self.terrain.update(
                aircraft_alt_ft=self.pfd.pressure_alt_ft,
                aircraft_lat=39.1031,
                aircraft_lon=-84.5120,
            )
            self.draw_terrain_status_box(painter, terrain_state, width, height)
            self.draw_terrain_alert(painter, terrain_state, width, height)

        if features.show_obstacles:
            obstacle_state = self.obstacles.update(
                aircraft_lat=39.1031,
                aircraft_lon=-84.5120,
                aircraft_alt_ft=self.pfd.pressure_alt_ft,
            )
            self.draw_obstacle_overlay(painter, obstacle_state, width, height)

        if features.show_traffic and self.config.stratux.enabled:
            self.draw_traffic_overlay(painter, self.stratux.read(), width, height)

        if features.show_weather:
            self.draw_weather_overlay(painter, self.weather.read(), width, height)

        draw_master_warning_strip(painter, self.engine_data, width)
        
        if self.current_page == "EMS_TREND":
            painter = QPainter(self)
            self.ems_trend_page.draw(
                painter,
                self.width(),
                self.height(),
            )
            draw_master_warning_strip(painter, self.engine_data, self.width())
            painter.end()
            return

        painter.end()

    def draw_background(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(5, 5, 8))

    def draw_synthetic_vision(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        scene = self.synthetic_vision.update(pfd)
        center_x = width // 2
        center_y = height // 2

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(-getattr(pfd, "roll_deg", 0.0))

        painter.fillRect(-width, -height * 2, width * 2, height * 2, QColor(*scene.sky_color))
        painter.fillRect(-width, 0, width * 2, height * 2, QColor(*scene.ground_color))

        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(-width, 0, width, 0)
        painter.restore()

        for obj in scene.objects or []:
            x, y = project_object_to_screen(
                obj.rel_bearing_deg,
                obj.elevation_angle_deg,
                width,
                height,
                obj.distance_nm,
            )

            if not (0 <= x <= width and 0 <= y <= height):
                continue

            if obj.kind == "runway":
                runway_w = int(120 * obj.size)
                runway_h = int(35 * obj.size)

                painter.setPen(QPen(QColor(255, 255, 255), 3))
                painter.setBrush(QBrush(QColor(40, 40, 40)))
                painter.drawRect(x - runway_w // 2, y - runway_h // 2, runway_w, runway_h)

                painter.setPen(QPen(QColor(255, 255, 0), 2))
                painter.drawLine(x, y - runway_h // 2, x, y + runway_h // 2)

                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x - 20, y - runway_h // 2 - 8, obj.label)
            else:
                box_w = int(70 * obj.size)
                box_h = int(38 * obj.size)

                painter.setPen(QPen(QColor(0, 255, 0), 3))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRect(x - box_w // 2, y - box_h // 2, box_w, box_h)

                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.drawText(x - 20, y - box_h // 2 - 8, obj.label)

    def draw_attitude(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height // 2
        horizon_width = int(width * 0.58)
        horizon_height = int(height * 0.70)

        roll_deg = getattr(pfd, "roll_deg", 0.0)
        pitch_deg = getattr(pfd, "pitch_deg", 0.0)

        painter.save()
        painter.setClipRect(
            center_x - horizon_width // 2,
            center_y - horizon_height // 2,
            horizon_width,
            horizon_height,
        )

        painter.translate(center_x, center_y)
        painter.rotate(-roll_deg)
        painter.translate(0, pitch_deg * 7.0)

        painter.fillRect(-horizon_width, -horizon_height * 2, horizon_width * 2, horizon_height * 2, QColor(25, 95, 180))
        painter.fillRect(-horizon_width, 0, horizon_width * 2, horizon_height * 2, QColor(125, 70, 25))

        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(-horizon_width, 0, horizon_width, 0)

        self.draw_pitch_ladder(painter)
        painter.restore()

        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.drawRect(
            center_x - horizon_width // 2,
            center_y - horizon_height // 2,
            horizon_width,
            horizon_height,
        )

        painter.setPen(QPen(QColor(255, 220, 0), 4))
        painter.drawLine(center_x - 90, center_y, center_x - 25, center_y)
        painter.drawLine(center_x + 25, center_y, center_x + 90, center_y)
        painter.drawLine(center_x, center_y - 8, center_x, center_y + 8)

        self.draw_roll_scale(painter, center_x, center_y, horizon_height)

    def draw_pitch_ladder(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        for pitch in range(-30, 35, 5):
            if pitch == 0:
                continue

            y = -pitch * 7.0
            line_half = 55 if pitch % 10 == 0 else 35
            painter.drawLine(int(-line_half), int(y), int(line_half), int(y))

            if pitch % 10 == 0:
                label = str(abs(pitch))
                painter.drawText(int(-line_half - 38), int(y + 5), label)
                painter.drawText(int(line_half + 12), int(y + 5), label)

    def draw_roll_scale(self, painter: QPainter, center_x: int, center_y: int, horizon_height: int) -> None:
        radius = int(horizon_height * 0.40)
        painter.setPen(QPen(QColor(255, 255, 255), 2))

        for deg in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:
            angle = radians(deg - 90)
            outer_x = center_x + int(radius * cos(angle))
            outer_y = center_y + int(radius * sin(angle))
            inner = radius - (18 if deg in [-60, -30, 0, 30, 60] else 10)
            inner_x = center_x + int(inner * cos(angle))
            inner_y = center_y + int(inner * sin(angle))
            painter.drawLine(inner_x, inner_y, outer_x, outer_y)

    def draw_airspeed_tape(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        tape_x, tape_y, tape_w = 30, 95, 105
        tape_h = height - 190
        center_y = tape_y + tape_h // 2
        ias = pfd.ias_kt

        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(20, 20, 25))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        for speed in range(int(ias - 50), int(ias + 55), 10):
            y = center_y - int((speed - ias) * 4.0)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(tape_x + tape_w - 35, y, tape_x + tape_w - 5, y)
                painter.drawText(tape_x + 10, y + 5, str(speed))

        painter.fillRect(tape_x + 5, center_y - 25, tape_w - 10, 50, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(tape_x + 5, center_y - 25, tape_w - 10, 50)
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(
            QRectF(tape_x + 5, center_y - 25, tape_w - 10, 50),
            Qt.AlignmentFlag.AlignCenter,
            f"{ias:.0f}",
        )

    def draw_altitude_tape(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        tape_w = 120
        tape_x = width - tape_w - 30
        tape_y = 95
        tape_h = height - 190
        center_y = tape_y + tape_h // 2
        alt = pfd.pressure_alt_ft

        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(20, 20, 25))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        start_alt = int((alt - 1000) // 100) * 100
        end_alt = int((alt + 1100) // 100) * 100

        for altitude in range(start_alt, end_alt, 100):
            y = center_y - int(((altitude - alt) / 100.0) * 22.0)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(tape_x + 5, y, tape_x + 35, y)
                painter.drawText(tape_x + 42, y + 5, str(altitude))

        painter.fillRect(tape_x + 5, center_y - 25, tape_w - 10, 50, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(tape_x + 5, center_y - 25, tape_w - 10, 50)
        painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        painter.drawText(
            QRectF(tape_x + 5, center_y - 25, tape_w - 10, 50),
            Qt.AlignmentFlag.AlignCenter,
            f"{alt:.0f}",
        )

    def draw_vsi(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        x = width - 180
        y = 120
        h = height - 240
        center_y = y + h // 2

        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawLine(x, y, x, y + h)

        clamped_vsi = max(-2000.0, min(2000.0, pfd.vsi_fpm))
        pointer_y = center_y - int((clamped_vsi / 2000.0) * (h / 2))

        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.setPen(QPen(QColor(0, 255, 255), 2))
        painter.drawPolygon(
            QPolygonF([
                point(x - 18, pointer_y),
                point(x - 38, pointer_y - 10),
                point(x - 38, pointer_y + 10),
            ])
        )

    def draw_heading_strip(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        strip_w = 500
        strip_h = 70
        strip_x = width // 2 - strip_w // 2
        strip_y = height - 95
        center_x = strip_x + strip_w // 2

        heading = pfd.heading_deg
        bearing = pfd.bearing_deg
        desired_track = pfd.desired_track_deg
        pixels_per_deg = 6.0

        painter.fillRect(strip_x, strip_y, strip_w, strip_h, QColor(15, 15, 20))
        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.drawRect(strip_x, strip_y, strip_w, strip_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        for hdg in range(int(heading - 50), int(heading + 55), 10):
            normalized = hdg % 360
            x = center_x + int((hdg - heading) * pixels_per_deg)
            if strip_x < x < strip_x + strip_w:
                painter.drawLine(x, strip_y + 5, x, strip_y + 25)
                painter.drawText(x - 18, strip_y + 50, heading_label(normalized))

        self.draw_heading_pointer(painter, center_x, strip_y)
        self.draw_bearing_pointer(painter, bearing, heading, center_x, strip_x, strip_y, strip_w, strip_h, pixels_per_deg)
        self.draw_desired_track_pointer(painter, desired_track, heading, center_x, strip_x, strip_y, strip_w, pixels_per_deg)

    def draw_heading_pointer(self, painter: QPainter, center_x: int, strip_y: int) -> None:
        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawPolygon(
            QPolygonF([
                point(center_x, strip_y + 5),
                point(center_x - 10, strip_y + 25),
                point(center_x + 10, strip_y + 25),
            ])
        )

    def draw_bearing_pointer(
        self,
        painter: QPainter,
        bearing: float,
        heading: float,
        center_x: int,
        strip_x: int,
        strip_y: int,
        strip_w: int,
        strip_h: int,
        pixels_per_deg: float,
    ) -> None:
        bearing_error = (bearing - heading + 180.0) % 360.0 - 180.0
        bearing_x = center_x + int(bearing_error * pixels_per_deg)

        if strip_x <= bearing_x <= strip_x + strip_w:
            painter.setBrush(QBrush(QColor(255, 0, 255)))
            painter.setPen(QPen(QColor(255, 0, 255), 2))
            painter.drawPolygon(
                QPolygonF([
                    point(bearing_x, strip_y + strip_h - 5),
                    point(bearing_x - 10, strip_y + strip_h - 25),
                    point(bearing_x + 10, strip_y + strip_h - 25),
                ])
            )
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(bearing_x - 18, strip_y + strip_h - 30, "BRG")

    def draw_desired_track_pointer(
        self,
        painter: QPainter,
        desired_track: float,
        heading: float,
        center_x: int,
        strip_x: int,
        strip_y: int,
        strip_w: int,
        pixels_per_deg: float,
    ) -> None:
        dtk_error = (desired_track - heading + 180.0) % 360.0 - 180.0
        dtk_x = center_x + int(dtk_error * pixels_per_deg)

        if strip_x <= dtk_x <= strip_x + strip_w:
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawPolygon(
                QPolygonF([
                    point(dtk_x, strip_y + 5),
                    point(dtk_x - 10, strip_y + 25),
                    point(dtk_x + 10, strip_y + 25),
                ])
            )
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(dtk_x - 16, strip_y + 38, "DTK")

    def draw_hsi_compass_rose(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height - 170
        radius = 95

        heading = pfd.heading_deg
        desired_track = pfd.desired_track_deg
        bearing = pfd.bearing_deg

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        for deg in range(0, 360, 30):
            relative = (deg - heading + 360) % 360
            angle = radians(relative - 90)

            outer_x = center_x + int(cos(angle) * radius)
            outer_y = center_y + int(sin(angle) * radius)
            inner_x = center_x + int(cos(angle) * (radius - 10))
            inner_y = center_y + int(sin(angle) * (radius - 10))

            painter.drawLine(inner_x, inner_y, outer_x, outer_y)

            label_x = center_x + int(cos(angle) * (radius - 25))
            label_y = center_y + int(sin(angle) * (radius - 25))

            painter.drawText(label_x - 10, label_y + 5, heading_label(deg))

        dtk_relative = (desired_track - heading + 360) % 360
        dtk_angle = radians(dtk_relative - 90)

        cdi_offset = max(-1.0, min(1.0, pfd.cdi)) * 35
        offset_angle = dtk_angle + radians(90)
        offset_x = int(cos(offset_angle) * cdi_offset)
        offset_y = int(sin(offset_angle) * cdi_offset)

        painter.setPen(QPen(QColor(0, 255, 0), 3))
        painter.drawLine(
            center_x + offset_x,
            center_y + offset_y,
            center_x + offset_x + int(cos(dtk_angle) * radius),
            center_y + offset_y + int(sin(dtk_angle) * radius),
        )
        painter.drawLine(
            center_x + offset_x,
            center_y + offset_y,
            center_x + offset_x - int(cos(dtk_angle) * radius),
            center_y + offset_y - int(sin(dtk_angle) * radius),
        )

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        for dot in [-2, -1, 1, 2]:
            dot_x = center_x + int(cos(offset_angle) * dot * 18)
            dot_y = center_y + int(sin(offset_angle) * dot * 18)
            painter.drawEllipse(dot_x - 3, dot_y - 3, 6, 6)

        brg_relative = (bearing - heading + 360) % 360
        brg_angle = radians(brg_relative - 90)

        painter.setPen(QPen(QColor(255, 0, 255), 3))
        painter.drawLine(
            center_x,
            center_y,
            center_x + int(cos(brg_angle) * (radius - 15)),
            center_y + int(sin(brg_angle) * (radius - 15)),
        )

        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawPolygon(
            QPolygonF([
                point(center_x, center_y - 12),
                point(center_x - 8, center_y + 10),
                point(center_x + 8, center_y + 10),
            ])
        )

        if self.config.obs.enabled:
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 0))
            painter.drawText(center_x - 38, center_y + radius + 22, f"OBS {self.config.obs.selected_course_deg:.0f}°")

    def draw_turn_and_slip(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        center_x = width // 2
        y = 78

        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawLine(center_x - 120, y, center_x + 120, y)
        painter.drawLine(center_x - 80, y - 8, center_x - 80, y + 8)
        painter.drawLine(center_x + 80, y - 8, center_x + 80, y + 8)

        ratio = max(-1.5, min(1.5, pfd.turn_rate_deg_sec / 3.0))
        pointer_x = center_x + int(ratio * 80)

        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawEllipse(pointer_x - 7, y - 7, 14, 14)

        ball_y = y + 45
        ball_x = center_x + int(pfd.slip_skid * 70)

        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.drawLine(center_x - 80, ball_y, center_x + 80, ball_y)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(ball_x - 10, ball_y - 10, 20, 20)

    def draw_nav_cdi_vdi(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        features = self.config.features
        center_x = width // 2
        center_y = height // 2

        if features.show_cdi:
            cdi_y = center_y + 185
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(center_x - 125, cdi_y, center_x + 125, cdi_y)

            cdi_x = center_x + int(max(-1.0, min(1.0, pfd.cdi)) * 100)
            painter.setBrush(QBrush(QColor(255, 0, 255)))
            painter.setPen(QPen(QColor(255, 0, 255), 2))
            painter.drawRect(cdi_x - 6, cdi_y - 28, 12, 56)

        if features.show_vdi and self.config.vnav.enabled:
            vdi_x = center_x + 290
            vdi_y = center_y - int(max(-1.0, min(1.0, pfd.vdi)) * 90)

            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawPolygon(
                QPolygonF([
                    point(vdi_x, vdi_y),
                    point(vdi_x + 22, vdi_y - 12),
                    point(vdi_x + 22, vdi_y + 12),
                ])
            )

    def draw_top_data_bar(self, painter: QPainter, pfd: FlightData, width: int) -> None:
        painter.fillRect(0, 0, width, 55, QColor(0, 0, 0))
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        parts = []

        if self.config.features.show_tas:
            parts.append(f"TAS {pfd.tas_kt:.0f} KT")
        if self.config.features.show_ground_speed:
            parts.append(f"GS {pfd.ground_speed_kt:.0f} KT")
        if self.config.features.show_wind:
            parts.append(f"WIND {pfd.wind_direction_deg:.0f}°/{pfd.wind_speed_kt:.0f} KT")

        painter.drawText(QRectF(0, 0, width, 55), Qt.AlignmentFlag.AlignCenter, "    ".join(parts))

    def draw_bottom_data_bar(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        painter.fillRect(0, height - 35, width, 35, QColor(0, 0, 0))
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        parts = [
            f"TRK {pfd.track_deg:.0f}°",
            f"BRG {pfd.bearing_deg:.0f}°",
            f"DTK {pfd.desired_track_deg:.0f}°",
            f"OBS {self.config.obs.selected_course_deg:.0f}°" if self.config.obs.enabled else "",
            f"CDI {pfd.cdi:+.2f} NM",
        ]

        parts = [part for part in parts if part]

        if self.config.features.show_vdi and self.config.vnav.enabled:
            parts.append(f"VDI {pfd.vdi:+.2f}°")

        painter.drawText(QRectF(0, height - 35, width, 35), Qt.AlignmentFlag.AlignCenter, "    ".join(parts))

    def draw_vnav_info_box(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        box_x = width - 250
        box_y = 265
        box_w = 220
        box_h = 105

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 25, "VNAV")
        painter.drawText(box_x + 10, box_y + 50, f"TGT ALT {pfd.glidepath_target_alt_ft:.0f}")
        painter.drawText(box_x + 10, box_y + 75, f"ALT ERR {pfd.glidepath_alt_error_ft:+.0f}")
        painter.drawText(box_x + 10, box_y + 100, f"GP {self.config.vnav.glidepath_angle_deg:.1f}°")

    def draw_waypoint_info_box(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        box_x = width // 2 - 120
        box_y = 60
        box_w = 240
        box_h = 85
        waypoint_id = self.config.navigation.selected_waypoint_id

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 25, f"WPT {waypoint_id}")

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 52, f"BRG {pfd.bearing_deg:.0f}°")
        painter.drawText(box_x + 120, box_y + 52, f"DIS {pfd.distance_to_waypoint_nm:.1f}NM")
        painter.drawText(box_x + 10, box_y + 75, f"CRS ERR {pfd.course_error_deg:+.0f}°")

    def draw_navigation_status_box(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        active_leg = self.route_manager.get_active_leg()
        waypoint_id = self.config.navigation.selected_waypoint_id

        box_x = width // 2 - 150
        box_y = 150
        box_w = 300
        box_h = 90

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(0, 255, 0))

        if active_leg is not None:
            painter.drawText(box_x + 10, box_y + 25, f"ACTIVE LEG {active_leg.from_ident} → {active_leg.to_ident}")
        else:
            painter.drawText(box_x + 10, box_y + 25, f"DIRECT TO {waypoint_id}")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 52, f"DTK {pfd.desired_track_deg:.0f}°")
        painter.drawText(box_x + 120, box_y + 52, f"BRG {pfd.bearing_deg:.0f}°")
        painter.drawText(box_x + 10, box_y + 76, f"DIS {pfd.distance_to_waypoint_nm:.1f} NM")

    def draw_nearest_airports_overlay(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        nearest = self.database.nearest_airports(39.1031, -84.5120, max_results=5)

        box_x, box_y, box_w, box_h = 20, height - 210, 330, 165
        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        y = box_y + 28
        painter.drawText(box_x + 10, y, "NEAREST AIRPORTS")
        y += 25

        for distance_nm, airport in nearest:
            painter.drawText(box_x + 10, y, f"{airport.ident:<5} {distance_nm:>4.1f}NM {airport.name[:24]}")
            y += 22

    def draw_moving_map_overlay(self, painter: QPainter, map_state, width: int, height: int) -> None:
        box_x = 20
        box_y = 300
        box_w = 300
        box_h = 220

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 24, f"MAP {map_state.range_nm:.0f} NM")

        center_x = box_x + box_w // 2
        center_y = box_y + box_h // 2

        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawPolygon(
            QPolygonF([
                point(center_x, center_y - 12),
                point(center_x - 8, center_y + 10),
                point(center_x + 8, center_y + 10),
            ])
        )

        radius = min(box_w, box_h) * 0.42

        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawEllipse(center_x - int(radius), center_y - int(radius), int(radius * 2), int(radius * 2))

        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))

        for airport in map_state.airports:
            if airport.distance_nm > map_state.range_nm:
                continue

            scale = airport.distance_nm / map_state.range_nm
            angle = radians(airport.bearing_deg - 90)

            airport_x = center_x + int(cos(angle) * radius * scale)
            airport_y = center_y + int(sin(angle) * radius * scale)

            painter.setPen(QPen(QColor(0, 255, 255), 2))
            painter.drawEllipse(airport_x - 3, airport_y - 3, 6, 6)
            painter.drawText(airport_x + 5, airport_y, airport.ident)

    def draw_route_overlay(self, painter: QPainter, width: int, height: int) -> None:
        route = self.route_manager.load_route()
        active_leg = self.route_manager.get_active_leg()

        box_x, box_y, box_w, box_h = width - 360, 120, 340, 135
        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 25, f"ROUTE: {route.get('route_id', 'NO ROUTE')}")
        painter.drawText(box_x + 10, box_y + 55, " → ".join(route.get("waypoints", []))[:35])

        if active_leg:
            painter.drawText(box_x + 10, box_y + 85, f"LEG: {active_leg.from_ident} → {active_leg.to_ident}")
            painter.drawText(box_x + 10, box_y + 112, f"DTK: {active_leg.desired_track_deg:.0f}°")

    def draw_selected_airport_info(self, painter: QPainter, width: int, height: int) -> None:
        airport_id = self.config.navigation.selected_waypoint_id
        airport = self.database.get_airport(airport_id)

        if airport is None:
            return

        runway = self.database.best_runway(airport_id)
        freqs = self.database.get_frequencies(airport_id)

        box_x = width - 360
        box_y = height - 350
        box_w = 340
        box_h = 300

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 25, f"{airport.ident} - {airport.name[:26]}")
        painter.drawText(box_x + 10, box_y + 55, f"Elev: {airport.elevation_ft:.0f} ft")

        if runway:
            painter.drawText(box_x + 10, box_y + 85, f"RWY {runway.le_ident}/{runway.he_ident}")
            painter.drawText(box_x + 10, box_y + 110, f"{runway.length_ft:.0f} x {runway.width_ft:.0f} ft {runway.surface[:10]}")

        y = box_y + 145
        for freq in freqs[:5]:
            painter.drawText(box_x + 10, y, f"{freq.type}: {freq.frequency_mhz:.3f}")
            y += 22

    def draw_startup_status_box(self, painter: QPainter, width: int, height: int) -> None:
        status = self.startup_status

        box_x = 20
        box_y = 20
        box_w = 280
        box_h = 65

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))

        color = QColor(0, 255, 0) if status.database_ok and status.config_ok else QColor(255, 0, 0)

        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 24, status.status_text)

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 50, f"APT {status.airports_loaded}  NAV {status.navaids_loaded}")

    def draw_sensor_status_panel(self, painter: QPainter, width: int, height: int) -> None:
        box_x = 310
        box_y = 20
        box_w = 300
        box_h = 90

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        mode_text = "HARDWARE" if self.use_hardware else "SIM"
        painter.setPen(QColor(0, 255, 0) if self.use_hardware else QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 24, f"SENSOR MODE: {mode_text}")

        if not self.use_hardware:
            painter.setPen(QColor(0, 180, 255))
            painter.drawText(box_x + 10, box_y + 52, "SIM DATA ACTIVE")
            return

        status = getattr(self.sensors, "status", None)

        if status is None:
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(box_x + 10, box_y + 52, "NO SENSOR STATUS")
            return

        def ok_text(label: str, ok: bool) -> str:
            return f"{label}:{'OK' if ok else 'OFF'}"

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            box_x + 10,
            box_y + 52,
            "  ".join([
                ok_text("AHRS", status.bno085_ok),
                ok_text("BARO", status.baro_ok),
                ok_text("IAS", status.airspeed_ok),
            ]),
        )
        painter.drawText(box_x + 10, box_y + 76, ok_text("GPS", status.gps_ok))

    def draw_sim_profile_box(self, painter: QPainter, width: int, height: int) -> None:
        if self.use_hardware:
            return

        profile = self.config.simulation.profile.upper()

        box_x = 620
        box_y = 20
        box_w = 230
        box_h = 65

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 25, "SIM PROFILE")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 50, profile)

    def draw_terrain_status_box(self, painter: QPainter, terrain_state, width: int, height: int) -> None:
        box_x = 20
        box_y = 95
        box_w = 230
        box_h = 90

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))

        if terrain_state.warning_level == "red":
            color = QColor(255, 0, 0)
        elif terrain_state.warning_level == "yellow":
            color = QColor(255, 220, 0)
        else:
            color = QColor(0, 255, 0)

        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 25, "TERRAIN")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 52, f"ELEV {terrain_state.terrain_elevation_ft:.0f} FT")
        painter.drawText(box_x + 10, box_y + 76, f"CLR {terrain_state.clearance_ft:.0f} FT")

    def draw_terrain_alert(self, painter: QPainter, terrain_state, width: int, height: int) -> None:
        if terrain_state.warning_level == "none":
            return

        color = QColor(255, 0, 0) if terrain_state.warning_level == "red" else QColor(255, 220, 0)

        painter.setPen(QPen(color, 3))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 55, width, 40), Qt.AlignmentFlag.AlignCenter, f"TERRAIN {terrain_state.clearance_ft:.0f} FT")

    def draw_obstacle_overlay(self, painter: QPainter, obstacle_state, width: int, height: int) -> None:
        if not obstacle_state.nearby:
            return

        box_x = 20
        box_y = 195
        box_w = 260
        box_h = 90

        color = QColor(255, 0, 0) if obstacle_state.warning else QColor(255, 220, 0)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 25, "OBSTACLE")

        obstacle = obstacle_state.nearby[0]

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 52, f"{obstacle.ident}")
        painter.drawText(box_x + 10, box_y + 76, f"{obstacle.distance_nm:.1f}NM BRG {obstacle.bearing_deg:.0f}°")

    def draw_safe_taxi_map(self, painter: QPainter, taxi_state, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(15, 15, 15))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(30, 45, f"SAFE TAXI - {taxi_state.airport_id}")

    def draw_traffic_overlay(self, painter: QPainter, stratux_state, width: int, height: int) -> None:
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(0, 255, 255) if stratux_state.ok else QColor(255, 180, 0))
        painter.drawText(width - 230, 80, "STRATUX ONLINE" if stratux_state.ok else "STRATUX OFFLINE")

    def draw_weather_overlay(self, painter: QPainter, weather_state, width: int, height: int) -> None:
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(0, 255, 0) if weather_state.ok else QColor(255, 180, 0))
        painter.drawText(width - 230, 105, "WX ONLINE" if weather_state.ok else "WX WAITING")


def point(x: float, y: float) -> QPointF:
    return QPointF(float(x), float(y))


def heading_label(heading: int) -> str:
    heading = heading % 360

    if heading == 0:
        return "N"
    if heading == 90:
        return "E"
    if heading == 180:
        return "S"
    if heading == 270:
        return "W"

    return f"{heading // 10:02d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blake PFD visual demo")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--sim", action="store_true", help="Run using simulated sensor data")
    mode_group.add_argument("--hardware", action="store_true", help="Run using real hardware sensor readers")

    parser.add_argument("--replay-log", help="Replay a recorded flight log CSV")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    app = QApplication(sys.argv)
    window = BlakePfdDemo(
        use_hardware=args.hardware,
        replay_log=args.replay_log,
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()