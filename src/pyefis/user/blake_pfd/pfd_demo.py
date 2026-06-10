"""
Blake PFD visual demo.

Standalone PyQt6 display that uses simulated sensor data.

Run later on Raspberry Pi with:
    python src/pyefis/user/blake_pfd/pfd_demo.py

In Codespaces, use:
    python -m compileall src

because Codespaces may not support the full Qt display environment.
"""

from __future__ import annotations
from pyefis.user.blake_pfd.synthetic_vision import SyntheticVisionComputer, project_object_to_screen
from pyefis.user.blake_pfd.safe_taxi import SafeTaxiComputer
import argparse
import sys
from math import cos, radians, sin
from pyefis.user.blake_pfd.stratux_reader import StratuxReader
from pyefis.user.blake_pfd.weather_reader import WeatherReader

from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF
from PyQt6.QtWidgets import QApplication, QWidget

from pyefis.user.blake_pfd.airdata import AirDataComputer, PfdData
from pyefis.user.blake_pfd.sensors_sim import SimulatedSensorSource
from pyefis.user.blake_pfd.hardware_readers import BlakeHardwareSensorSource
from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.database_importer import AviationDatabase

class BlakePfdDemo(QWidget):
    def draw_weather_overlay(self, painter: QPainter, weather_state, width: int, height: int) -> None:
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        if not weather_state.ok:
            painter.setPen(QColor(255, 180, 0))
            painter.drawText(width - 230, 105, "WX WAITING")
            return

        painter.setPen(QColor(0, 255, 0))
        painter.drawText(width - 230, 105, "WX ONLINE")
    def draw_traffic_overlay(self, painter: QPainter, stratux_state, width: int, height: int) -> None:
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        if not stratux_state.ok:
            painter.setPen(QColor(255, 180, 0))
            painter.drawText(width - 230, 80, "STRATUX OFFLINE")
            return

        painter.setPen(QColor(0, 255, 255))
        painter.drawText(width - 230, 80, "STRATUX ONLINE")

        for target in stratux_state.traffic or []:
            painter.drawText(
                width - 230,
                105,
                f"{target.callsign} {target.distance_nm:.1f}NM {target.relative_alt_ft:+.0f}FT",
            )
    
    def draw_safe_taxi_map(self, painter: QPainter, taxi_state, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(15, 15, 15))

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(30, 45, f"SAFE TAXI - {taxi_state.airport_id}")

        center_x = width // 2
        center_y = height // 2

        # Simple airport diagram placeholder.
        painter.setPen(QPen(QColor(180, 180, 180), 8))
        painter.drawLine(center_x - 300, center_y, center_x + 300, center_y)

        painter.setPen(QPen(QColor(120, 120, 120), 5))
        painter.drawLine(center_x, center_y - 180, center_x, center_y + 180)
        painter.drawLine(center_x - 220, center_y + 120, center_x + 220, center_y + 120)

        # Ownship triangle.
        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))

        ownship = QPolygonF([
            point(center_x, center_y - 22),
            point(center_x - 14, center_y + 18),
            point(center_x + 14, center_y + 18),
        ])
        painter.drawPolygon(ownship)

        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(30, height - 40, "Taxi map placeholder - real airport database comes later")
    
    def draw_selected_airport_info(self, painter: QPainter, width: int, height: int) -> None:
        airport_id = self.config.navigation.selected_waypoint_id
        airport = self.database.get_airport(airport_id)
        runway = self.database.best_runway(airport_id)
        freqs = self.database.get_frequencies(airport_id)
        freq_y = box_y + 210
        for freq in freqs[:4]:
            painter.drawText(
                box_x + 10,
                freq_y,
                f"{freq.type}: {freq.frequency_mhz:.3f}",
            )
            freq_y += 22

        if airport is None:
            return

        box_x = width - 360
        box_y = height - 250
        box_w = 340
        box_h = 300

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 25, f"{airport.ident} - {airport.name[:26]}")

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 55, f"Elev: {airport.elevation_ft:.0f} ft")
        painter.drawText(box_x + 10, box_y + 80, f"Lat: {airport.lat_deg:.4f}")
        painter.drawText(box_x + 10, box_y + 105, f"Lon: {airport.lon_deg:.4f}")

        if runway is not None:
            painter.drawText(
                box_x + 10,
                box_y + 135,
                f"RWY {runway.le_ident}/{runway.he_ident}",
            )
            painter.drawText(
                box_x + 10,
                box_y + 160,
                f"{runway.length_ft:.0f} x {runway.width_ft:.0f} ft {runway.surface[:10]}",
            )
            painter.drawText(
                box_x + 10,
                box_y + 185,
                f"Hdg {runway.le_heading_deg:.0f}/{runway.he_heading_deg:.0f}",
            )

    def __init__(self, use_hardware: bool = False) -> None:
        super().__init__()

        mode_name = "Hardware" if use_hardware else "Simulator"
        self.config = load_config()
        self.database = AviationDatabase()
        self.database.load_all()
        self.setWindowTitle(f"Blake PFD Demo - {mode_name}")
        self.resize(self.config.display.width, self.config.display.height)

        if self.config.display.fullscreen:
            self.showFullScreen()

        if use_hardware:
            self.sensors = BlakeHardwareSensorSource()
        else:
            self.sensors = SimulatedSensorSource()

        self.airdata = AirDataComputer()
        self.synthetic_vision = SyntheticVisionComputer()
        self.safe_taxi = SafeTaxiComputer(auto_switch_groundspeed_kt=self.config.features.safe_taxi.auto_switch_groundspeed_kt)
        self.stratux = StratuxReader(
            host=self.config.stratux.host,
            port=self.config.stratux.gdl90_port,
        )
        self.weather = WeatherReader()
        self.pfd: PfdData | None = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)  # 20 Hz update
        

    def update_data(self) -> None:
        raw = self.sensors.read()
        self.pfd = self.airdata.update(raw)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        if self.pfd is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        self.draw_background(painter, width, height)

        features = self.config.features
        taxi_state = self.safe_taxi.update(self.pfd)

        if features.show_safe_taxi and taxi_state.active:
            self.draw_safe_taxi_map(painter, taxi_state, width, height)
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

        if features.show_turn_rate or features.show_slip_skid:
            self.draw_turn_and_slip(painter, self.pfd, width, height)

        if features.show_cdi or features.show_vdi:
            self.draw_nav_cdi_vdi(painter, self.pfd, width, height)

            self.draw_top_data_bar(painter, self.pfd, width)
            self.draw_bottom_data_bar(painter, self.pfd, width, height)
            
        if features.show_traffic and self.config.stratux.enabled:
            stratux_state = self.stratux.read()
            self.draw_traffic_overlay(painter, stratux_state, width, height)
        if features.show_weather:
            weather_state = self.weather.read()
            self.draw_weather_overlay(painter, weather_state, width, height)    
        if features.show_nearest_airports:
            self.draw_nearest_airports_overlay(painter, self.pfd, width, height)
        self.draw_selected_airport_info(painter, width, height)
        painter.end()

    def draw_background(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(5, 5, 8))

    def draw_attitude(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height // 2
        horizon_width = int(width * 0.58)
        horizon_height = int(height * 0.70)

        painter.save()

        painter.setClipRect(
            center_x - horizon_width // 2,
            center_y - horizon_height // 2,
            horizon_width,
            horizon_height,
        )

        painter.translate(center_x, center_y)
        painter.rotate(-pfd.roll_deg)

        pitch_pixels = pfd.pitch_deg * 7.0
        painter.translate(0, pitch_pixels)

        sky = QColor(25, 95, 180)
        ground = QColor(125, 70, 25)

        painter.fillRect(
            -horizon_width,
            -horizon_height * 2,
            horizon_width * 2,
            horizon_height * 2,
            sky,
        )

        painter.fillRect(
            -horizon_width,
            0,
            horizon_width * 2,
            horizon_height * 2,
            ground,
        )

        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(-horizon_width, 0, horizon_width, 0)

        self.draw_pitch_ladder(painter, horizon_width)

        painter.restore()

        # Border around attitude area
        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.drawRect(
            center_x - horizon_width // 2,
            center_y - horizon_height // 2,
            horizon_width,
            horizon_height,
        )

        # Fixed aircraft symbol
        painter.setPen(QPen(QColor(255, 220, 0), 4))
        painter.drawLine(center_x - 90, center_y, center_x - 25, center_y)
        painter.drawLine(center_x + 25, center_y, center_x + 90, center_y)
        painter.drawLine(center_x, center_y - 8, center_x, center_y + 8)

        # Roll pointer
        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        pointer = QPolygonF([
            point(center_x, center_y - int(horizon_height * 0.40)),
            point(center_x - 10, center_y - int(horizon_height * 0.40) + 20),
            point(center_x + 10, center_y - int(horizon_height * 0.40) + 20),
        ])
        painter.drawPolygon(pointer)

        self.draw_roll_scale(painter, center_x, center_y, horizon_height)

    def draw_pitch_ladder(self, painter: QPainter, horizon_width: int) -> None:
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

    def draw_roll_scale(
        self,
        painter: QPainter,
        center_x: int,
        center_y: int,
        horizon_height: int,
    ) -> None:
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

    def draw_synthetic_vision(
        self,
        painter: QPainter,
        pfd: PfdData,
        width: int,
        height: int,
    ) -> None:
        scene = self.synthetic_vision.update(pfd)

        center_x = width // 2
        center_y = height // 2

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(-pfd.roll_deg)

        sky = QColor(*scene.sky_color)
        ground = QColor(*scene.ground_color)

        painter.fillRect(-width, -height * 2, width * 2, height * 2, sky)
        painter.fillRect(-width, 0, width * 2, height * 2, ground)

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

            if 0 <= x <= width and 0 <= y <= height:
                box_w = int(70 * obj.size)
                box_h = int(38 * obj.size)

                painter.setPen(QPen(QColor(0, 255, 0), 3))
                painter.drawRect(x - box_w // 2, y - box_h // 2, box_w, box_h)

                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.drawText(x - 20, y - box_h // 2 - 8, obj.label)

    def draw_airspeed_tape(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        tape_x = 30
        tape_y = 95
        tape_w = 105
        tape_h = height - 190
        center_y = tape_y + tape_h // 2

        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(20, 20, 25))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        ias = pfd.ias_kt
        pixels_per_knot = 4.0

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        start_speed = int(ias - 50)
        end_speed = int(ias + 55)

        for speed in range(start_speed, end_speed, 10):
            y = center_y - int((speed - ias) * pixels_per_knot)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(tape_x + tape_w - 35, y, tape_x + tape_w - 5, y)
                painter.drawText(tape_x + 10, y + 5, str(speed))

        # Current IAS box
        painter.fillRect(tape_x + 5, center_y - 25, tape_w - 10, 50, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(tape_x + 5, center_y - 25, tape_w - 10, 50)
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(
            QRectF(tape_x + 5, center_y - 25, tape_w - 10, 50),
            Qt.AlignmentFlag.AlignCenter,
            f"{ias:.0f}",
        )

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(tape_x + 20, tape_y - 12, "IAS")

    def draw_altitude_tape(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        tape_w = 120
        tape_x = width - tape_w - 30
        tape_y = 95
        tape_h = height - 190
        center_y = tape_y + tape_h // 2

        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(20, 20, 25))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        alt = pfd.pressure_alt_ft
        pixels_per_100_ft = 22.0

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        start_alt = int((alt - 1000) // 100) * 100
        end_alt = int((alt + 1100) // 100) * 100

        for altitude in range(start_alt, end_alt, 100):
            y = center_y - int(((altitude - alt) / 100.0) * pixels_per_100_ft)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(tape_x + 5, y, tape_x + 35, y)
                painter.drawText(tape_x + 42, y + 5, str(altitude))

        # Current altitude box
        painter.fillRect(tape_x + 5, center_y - 25, tape_w - 10, 50, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(tape_x + 5, center_y - 25, tape_w - 10, 50)
        painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        painter.drawText(
            QRectF(tape_x + 5, center_y - 25, tape_w - 10, 50),
            Qt.AlignmentFlag.AlignCenter,
            f"{alt:.0f}",
        )

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(tape_x + 35, tape_y - 12, "ALT")

    def draw_vsi(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        x = width - 180
        y = 120
        h = height - 240
        center_y = y + h // 2

        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawLine(x, y, x, y + h)

        for vsi in [-2000, -1000, 0, 1000, 2000]:
            tick_y = center_y - int((vsi / 2000.0) * (h / 2))
            painter.drawLine(x - 10, tick_y, x + 10, tick_y)
            painter.setFont(QFont("Arial", 9))
            painter.drawText(x + 15, tick_y + 4, str(vsi))

        clamped_vsi = max(-2000.0, min(2000.0, pfd.vsi_fpm))
        pointer_y = center_y - int((clamped_vsi / 2000.0) * (h / 2))

        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.setPen(QPen(QColor(0, 255, 255), 2))
        tri = QPolygonF([
            point(x - 18, pointer_y),
            point(x - 38, pointer_y - 10),
            point(x - 38, pointer_y + 10),
        ])
        painter.drawPolygon(tri)

    def draw_heading_strip(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        strip_w = 500
        strip_h = 70
        strip_x = width // 2 - strip_w // 2
        strip_y = height - 95

        painter.fillRect(strip_x, strip_y, strip_w, strip_h, QColor(15, 15, 20))
        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.drawRect(strip_x, strip_y, strip_w, strip_h)

        heading = pfd.heading_deg
        bearing = getattr(pfd, "bearing_deg", heading)
        desired_track = getattr(pfd, "desired_track_deg", heading)
        pixels_per_deg = 6.0
        center_x = strip_x + strip_w // 2

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        for hdg in range(int(heading - 50), int(heading + 55), 10):
            normalized = hdg % 360
            x = center_x + int((hdg - heading) * pixels_per_deg)
            if strip_x < x < strip_x + strip_w:
                painter.drawLine(x, strip_y + 5, x, strip_y + 25)
                label = heading_label(normalized)
                painter.drawText(x - 18, strip_y + 50, label)

        # Heading pointer and current heading box
        painter.setBrush(QBrush(QColor(255, 220, 0)))
        pointer = QPolygonF([
            point(center_x, strip_y + 5),
            point(center_x - 10, strip_y + 25),
            point(center_x + 10, strip_y + 25),
        ])
        painter.drawPolygon(pointer)

        painter.fillRect(center_x - 45, strip_y - 38, 90, 34, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(center_x - 45, strip_y - 38, 90, 34)
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(
            QRectF(center_x - 45, strip_y - 38, 90, 34),
            Qt.AlignmentFlag.AlignCenter,
            f"{heading:.0f}°",
        )
            # Waypoint bearing pointer
        bearing_error = (bearing - heading + 180.0) % 360.0 - 180.0
        bearing_x = center_x + int(bearing_error * pixels_per_deg)

        if strip_x <= bearing_x <= strip_x + strip_w:
            painter.setBrush(QBrush(QColor(255, 0, 255)))
            painter.setPen(QPen(QColor(255, 0, 255), 2))

            wp_pointer = QPolygonF([
                point(bearing_x, strip_y + strip_h - 5),
                point(bearing_x - 10, strip_y + strip_h - 25),
                point(bearing_x + 10, strip_y + strip_h - 25),
            ])
            painter.drawPolygon(wp_pointer)

            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(bearing_x - 18, strip_y + strip_h - 30, "BRG")
                # Desired track pointer
        dtk_error = (desired_track - heading + 180.0) % 360.0 - 180.0
        dtk_x = center_x + int(dtk_error * pixels_per_deg)

        if strip_x <= dtk_x <= strip_x + strip_w:
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.setPen(QPen(QColor(0, 255, 0), 2))

            dtk_pointer = QPolygonF([
                point(dtk_x, strip_y + 5),
                point(dtk_x - 10, strip_y + 25),
                point(dtk_x + 10, strip_y + 25),
            ])
            painter.drawPolygon(dtk_pointer)

            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(dtk_x - 16, strip_y + 38, "DTK")
            
    def draw_turn_and_slip(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        center_x = width // 2
        y = 78

        # Turn rate bar
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawLine(center_x - 120, y, center_x + 120, y)
        painter.drawLine(center_x - 80, y - 8, center_x - 80, y + 8)
        painter.drawLine(center_x + 80, y - 8, center_x + 80, y + 8)
        painter.drawLine(center_x, y - 12, center_x, y + 12)

        ratio = max(-1.5, min(1.5, pfd.standard_rate_ratio))
        pointer_x = center_x + int(ratio * 80)

        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawEllipse(pointer_x - 7, y - 7, 14, 14)

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(center_x - 150, y + 30, "STD RATE")

        # Slip/skid ball
        ball_track_y = y + 45
        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.drawLine(center_x - 80, ball_track_y, center_x + 80, ball_track_y)
        painter.drawLine(center_x - 25, ball_track_y - 10, center_x - 25, ball_track_y + 10)
        painter.drawLine(center_x + 25, ball_track_y - 10, center_x + 25, ball_track_y + 10)

        ball_x = center_x + int(pfd.slip_skid * 70)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(ball_x - 10, ball_track_y - 10, 20, 20)

    def draw_nav_cdi_vdi(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        features = self.config.features
        center_x = width // 2
        center_y = height // 2

        if features.show_cdi:
            cdi_y = center_y + 185
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(center_x - 125, cdi_y, center_x + 125, cdi_y)

            for offset in [-100, -50, 0, 50, 100]:
                painter.drawEllipse(center_x + offset - 4, cdi_y - 4, 8, 8)

            cdi_x = center_x + int(max(-1.0, min(1.0, pfd.cdi_deflection_nm)) * 100)

            painter.setBrush(QBrush(QColor(255, 0, 255)))
            painter.setPen(QPen(QColor(255, 0, 255), 2))
            painter.drawRect(cdi_x - 6, cdi_y - 28, 12, 56)

            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(center_x - 160, cdi_y + 28, "CDI")

        if features.show_vdi:
            vdi_x = center_x + 290
            vdi_y_top = center_y - 120
            vdi_h = 240

            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(vdi_x, vdi_y_top, vdi_x, vdi_y_top + vdi_h)

            for offset in [-80, -40, 0, 40, 80]:
                painter.drawEllipse(vdi_x - 4, center_y + offset - 4, 8, 8)

            vdi_y = center_y - int(max(-1.0, min(1.0, pfd.vdi_deflection_deg)) * 90)

            painter.setBrush(QBrush(QColor(0, 255, 0)))
            tri = QPolygonF([
                point(vdi_x, vdi_y),
                point(vdi_x + 22, vdi_y - 12),
                point(vdi_x + 22, vdi_y + 12),
            ])
            painter.drawPolygon(tri)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(vdi_x + 18, vdi_y_top - 10, "VDI")
            
    def draw_nearest_airports_overlay(self, painter: QPainter, pfd, width: int, height: int) -> None:
        aircraft_lat = getattr(pfd, "gps_lat_deg", 39.1031)
        aircraft_lon = getattr(pfd, "gps_lon_deg", -84.5120)

        nearest = self.database.nearest_airports(
            aircraft_lat,
            aircraft_lon,
            max_results=5,
        )

        box_x = 20
        box_y = height - 210
        box_w = 330
        box_h = 165

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 24, "NEAREST AIRPORTS")

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        y = box_y + 50
        for distance_nm, airport in nearest:
            painter.drawText(
                box_x + 10,
                y,
                f"{airport.ident:<5} {distance_nm:>4.1f}NM {airport.name[:24]}",
            )
            y += 22

    def draw_top_data_bar(self, painter: QPainter, pfd: PfdData, width: int) -> None:
        painter.fillRect(0, 0, width, 55, QColor(0, 0, 0))
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        features = self.config.features
        parts = []

        if features.show_tas:
            parts.append(f"TAS {pfd.tas_kt:.0f} KT")
        if features.show_ground_speed:
            parts.append(f"GS {pfd.ground_speed_kt:.0f} KT")
        if features.show_oat:
            parts.append(f"OAT {pfd.outside_air_temp_c:.0f} C")
        if features.show_wind:
            parts.append(f"WIND {pfd.wind_direction_deg:.0f}°/{pfd.wind_speed_kt:.0f} KT")

        painter.drawText(
            QRectF(0, 0, width, 55),
            Qt.AlignmentFlag.AlignCenter,
            "    ".join(parts),
        )

    def draw_bottom_data_bar(self, painter: QPainter, pfd: PfdData, width: int, height: int) -> None:
        painter.fillRect(0, height - 35, width, 35, QColor(0, 0, 0))
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        features = self.config.features
        parts = []

        if features.show_heading:
            parts.append(f"TRK {pfd.gps_track_deg:.0f}°")
        if features.show_hsi:
            parts.append(f"BRG {pfd.waypoint_bearing_deg:.0f}°")
            parts.append(f"DTK {pfd.desired_track_deg:.0f}°")
        if features.show_cdi:
            parts.append(f"CDI {pfd.cdi_deflection_nm:+.2f} NM")
        if features.show_vdi:
            parts.append(f"VDI {pfd.vdi_deflection_deg:+.2f}°")

        painter.drawText(
            QRectF(0, height - 35, width, 35),
            Qt.AlignmentFlag.AlignCenter,
            "    ".join(parts),
        )
def point(x: float, y: float):
    from PyQt6.QtCore import QPointF
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
    mode_group.add_argument(
        "--sim",
        action="store_true",
        help="Run using simulated sensor data",
    )
    mode_group.add_argument(
        "--hardware",
        action="store_true",
        help="Run using real hardware sensor readers",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    use_hardware = args.hardware

    app = QApplication(sys.argv)
    window = BlakePfdDemo(use_hardware=use_hardware)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
