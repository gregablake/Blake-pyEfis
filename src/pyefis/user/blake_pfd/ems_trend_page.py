from __future__ import annotations

from collections import deque

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen

from pyefis.user.blake_pfd.engine_data import EngineData


class EmsTrendPage:
    def __init__(self, max_samples: int = 300) -> None:
        self.samples: deque[EngineData] = deque(
            maxlen=max_samples
        )
        self.sensor_statuses: deque = deque(
            maxlen=max_samples
        )
        self.data_available = True
        self.fault_message = ""

    def add_sample(
        self,
        engine: EngineData,
        sensor_status=None,
    ) -> None:
        self.samples.append(engine)
        self.sensor_statuses.append(sensor_status)
        self.data_available = True
        self.fault_message = ""

    def set_data_available(
        self,
        available: bool,
        message: str = "",
    ) -> None:
        self.data_available = bool(available)
        self.fault_message = (
            ""
            if self.data_available
            else str(message)
        )

    def draw(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(0, 0, 0))

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "EMS TREND PAGE",
        )

        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(40, 90, f"Samples: {len(self.samples)}")

        if not self.data_available:
            painter.setPen(QColor(255, 80, 80))
            painter.setFont(
                QFont("Arial", 18, QFont.Weight.Bold)
            )
            painter.drawText(
                QRectF(0, 78, width, 40),
                Qt.AlignmentFlag.AlignCenter,
                self.fault_message or "EMS DATA UNAVAILABLE",
            )

        chart_w = (width - 100) // 2
        chart_h = 185

        self.draw_cht_chart(painter, 40, 125, chart_w, chart_h)
        self.draw_egt_chart(painter, 60 + chart_w, 125, chart_w, chart_h)
        self.draw_engine_chart(painter, 40, 345, chart_w, chart_h)
        self.draw_fuel_chart(painter, 60 + chart_w, 345, chart_w, chart_h)

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(40, height - 40, "E = EMS    P = PFD    T = TRENDS")

    def draw_cht_chart(self, painter: QPainter, x: int, y: int, w: int, h: int) -> None:
        self.draw_chart_frame(painter, x, y, w, h, "CHT 1-6", "250-450°F")

        colors = [
            QColor(0, 255, 0),
            QColor(0, 180, 255),
            QColor(255, 255, 0),
            QColor(255, 120, 0),
            QColor(255, 0, 255),
            QColor(255, 255, 255),
        ]

        for cylinder in range(6):
            values = []

            for sample_index, sample in enumerate(self.samples):
                if len(sample.cht_f) <= cylinder:
                    continue

                status = (
                    self.sensor_statuses[sample_index]
                    if sample_index < len(self.sensor_statuses)
                    else None
                )

                if status is not None:
                    if cylinder >= len(status.cht):
                        continue

                    channel_status = status.cht[cylinder]

                    if not (
                        channel_status.valid
                        and channel_status.fresh
                    ):
                        continue

                values.append(sample.cht_f[cylinder])

            self.draw_line(
                painter,
                values,
                x,
                y,
                w,
                h,
                250,
                450,
                colors[cylinder],
            )

    def draw_egt_chart(self, painter: QPainter, x: int, y: int, w: int, h: int) -> None:
        self.draw_chart_frame(painter, x, y, w, h, "EGT 1-2", "1000-1650°F")

        colors = [
            QColor(255, 120, 0),
            QColor(255, 255, 255),
        ]

        for probe in range(2):
            values = []

            for sample_index, sample in enumerate(self.samples):
                if len(sample.egt_f) <= probe:
                    continue

                status = (
                    self.sensor_statuses[sample_index]
                    if sample_index < len(self.sensor_statuses)
                    else None
                )

                if status is not None:
                    if probe >= len(status.egt):
                        continue

                    channel_status = status.egt[probe]

                    if not (
                        channel_status.valid
                        and channel_status.fresh
                    ):
                        continue

                values.append(sample.egt_f[probe])

            self.draw_line(
                painter,
                values,
                x,
                y,
                w,
                h,
                1000,
                1650,
                colors[probe],
            )

    def draw_engine_chart(self, painter: QPainter, x: int, y: int, w: int, h: int) -> None:
        self.draw_chart_frame(painter, x, y, w, h, "OIL / VOLTS", "scaled")

        oil_temp = []
        oil_psi = []
        volts = []

        for sample_index, sample in enumerate(self.samples):
            status = (
                self.sensor_statuses[sample_index]
                if sample_index < len(self.sensor_statuses)
                else None
            )

            if (
                status is None
                or (
                    status.oil_temperature.valid
                    and status.oil_temperature.fresh
                )
            ):
                oil_temp.append(sample.oil_temp_f)

            if (
                status is None
                or (
                    status.oil_pressure.valid
                    and status.oil_pressure.fresh
                )
            ):
                oil_psi.append(sample.oil_pressure_psi)

            if (
                status is None
                or (
                    status.volts.valid
                    and status.volts.fresh
                )
            ):
                volts.append(sample.volts)

        self.draw_line(
            painter,
            oil_temp,
            x,
            y,
            w,
            h,
            100,
            260,
            QColor(255, 120, 0),
        )

        self.draw_line(
            painter,
            oil_psi,
            x,
            y,
            w,
            h,
            0,
            80,
            QColor(0, 255, 255),
        )

        self.draw_line(
            painter,
            volts,
            x,
            y,
            w,
            h,
            10,
            16,
            QColor(255, 255, 0),
        )

        self.draw_legend(
            painter,
            x,
            y,
            h,
            [
                ("OIL TEMP", QColor(255, 120, 0)),
                ("OIL PSI", QColor(0, 255, 255)),
                ("VOLTS", QColor(255, 255, 0)),
            ],
        )

    def draw_fuel_chart(self, painter: QPainter, x: int, y: int, w: int, h: int) -> None:
        self.draw_chart_frame(painter, x, y, w, h, "FUEL", "scaled")

        fuel_remaining = [sample.fuel_remaining_gal for sample in self.samples]
        fuel_flow = []

        for index, sample in enumerate(self.samples):
            status = None

            if index < len(self.sensor_statuses):
                status = self.sensor_statuses[index]

            if (
                status is None
                or (
                    status.fuel_flow.valid
                    and status.fuel_flow.fresh
                )
            ):
                fuel_flow.append(
                    sample.fuel_flow_gph
                )
        endurance = [sample.endurance_hr for sample in self.samples]

        self.draw_line(painter, fuel_remaining, x, y, w, h, 0, 30, QColor(0, 255, 0))
        self.draw_line(painter, fuel_flow, x, y, w, h, 0, 12, QColor(0, 180, 255))
        self.draw_line(painter, endurance, x, y, w, h, 0, 5, QColor(255, 255, 0))

        self.draw_legend(
            painter,
            x,
            y,
            h,
            [
                ("FUEL REM", QColor(0, 255, 0)),
                ("FLOW", QColor(0, 180, 255)),
                ("ENDUR", QColor(255, 255, 0)),
            ],
        )

    def draw_chart_frame(
        self,
        painter: QPainter,
        x: int,
        y: int,
        w: int,
        h: int,
        title: str,
        scale_text: str,
    ) -> None:
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawRect(x, y, w, h)

        painter.setPen(QColor(0, 180, 255))
        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(x + 10, y + 25, title)

        painter.setPen(QColor(130, 130, 130))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(x + w - 95, y + 25, scale_text)

        painter.setPen(QPen(QColor(40, 40, 40), 1))
        for i in range(1, 4):
            grid_y = y + int((h / 4) * i)
            painter.drawLine(x, grid_y, x + w, grid_y)

    def draw_legend(
        self,
        painter: QPainter,
        x: int,
        y: int,
        h: int,
        items: list[tuple[str, QColor]],
    ) -> None:
        legend_x = x + 12
        legend_y = y + h - 18

        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))

        for label, color in items:
            painter.setPen(color)
            painter.drawText(legend_x, legend_y, label)
            legend_x += 75

    def draw_line(
        self,
        painter: QPainter,
        values: list[float],
        x: int,
        y: int,
        w: int,
        h: int,
        min_value: float,
        max_value: float,
        color: QColor,
    ) -> None:
        if len(values) < 2:
            return

        plot_x = x + 32
        plot_y = y + 35
        plot_w = w - 55
        plot_h = h - 60

        painter.setPen(QPen(color, 2))

        max_points = len(values)

        for index in range(1, max_points):
            x1 = plot_x + int(((index - 1) / (max_points - 1)) * plot_w)
            x2 = plot_x + int((index / (max_points - 1)) * plot_w)

            y1 = self.value_to_y(values[index - 1], plot_y, plot_h, min_value, max_value)
            y2 = self.value_to_y(values[index], plot_y, plot_h, min_value, max_value)

            painter.drawLine(x1, y1, x2, y2)

    def value_to_y(
        self,
        value: float,
        plot_y: int,
        plot_h: int,
        min_value: float,
        max_value: float,
    ) -> int:
        ratio = (value - min_value) / (max_value - min_value)
        ratio = max(0.0, min(1.0, ratio))
        return plot_y + plot_h - int(ratio * plot_h)