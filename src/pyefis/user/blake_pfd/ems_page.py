from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen

from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.engine_data import EngineData


class EmsPage:
    def draw(
        self,
        painter: QPainter,
        aircraft,
        width: int,
        height: int,
        checklist=None,
        aircraft_recommendation=None,
        fault_message: str = "",
        sensor_status=None,
    ) -> None:
        engine_state = getattr(
            aircraft,
            "engine_state",
            None,
        )

        painter.fillRect(
            0,
            0,
            width,
            height,
            QColor(0, 0, 0),
        )

        painter.setPen(QColor(0, 255, 0))
        painter.setFont(
            QFont(
                "Arial",
                24,
                QFont.Weight.Bold,
            )
        )
        painter.drawText(
            QRectF(0, 20, width, 40),
            Qt.AlignmentFlag.AlignCenter,
            "ENGINE MONITORING SYSTEM",
        )

        if engine_state is None:
            painter.setPen(
                QColor(
                    255,
                    80,
                    80,
                )
            )
            painter.setFont(
                QFont(
                    "Arial",
                    28,
                    QFont.Weight.Bold,
                )
            )
            painter.drawText(
                QRectF(
                    0,
                    150,
                    width,
                    80,
                ),
                Qt.AlignmentFlag.AlignCenter,
                fault_message or "ENGINE DATA UNAVAILABLE",
            )
            return

        engine_advice = getattr(
            engine_state,
            "advice",
            None,
        )
        engine = engine_state.data
        engine_health = engine_state.health
        engine_analysis = engine_state.analysis
        engine_trend = engine_state.trend
        cylinders = engine_state.cylinders

        self.draw_annunciators(
            painter,
            engine,
            width,
            sensor_status=sensor_status,
        )
        self.draw_test_mode_label(painter, width)

        y = 105
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        self.draw_value(
            painter,
            40,
            y,
            "RPM",
            engine.rpm,
            "",
            self.rpm_color(engine.rpm),
            status=(
                sensor_status.rpm
                if sensor_status is not None
                else None
            ),
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "VOLTS",
            engine.volts,
            "V",
            self.voltage_color(engine.volts),
            decimals=1,
            status=(
                sensor_status.volts
                if sensor_status is not None
                else None
            ),
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "AMPS",
            engine.amps,
            "A",
            QColor(255, 255, 255),
            decimals=1,
            signed=True,
            status=(
                sensor_status.amps
                if sensor_status is not None
                else None
            ),
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "OIL PSI",
            engine.oil_pressure_psi,
            "",
            self.oil_pressure_color(
                engine.oil_pressure_psi,
                engine.rpm,
            ),
            status=(
                sensor_status.oil_pressure
                if sensor_status is not None
                else None
            ),
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "OIL TEMP",
            engine.oil_temp_f,
            "°F",
            self.oil_temp_color(engine.oil_temp_f),
            status=(
                sensor_status.oil_temperature
                if sensor_status is not None
                else None
            ),
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "FUEL PSI",
            engine.fuel_pressure_psi,
            "",
            QColor(255, 255, 255),
            decimals=1,
            status=(
                sensor_status.fuel_pressure
                if sensor_status is not None
                else None
            ),
        )
        y += 45

        fuel_color = self.fuel_color(engine)

        self.draw_value(
            painter,
            40,
            y,
            "FUEL FLOW",
            engine.fuel_flow_gph,
            "GPH",
            QColor(255, 255, 255),
            decimals=1,
            status=(
                sensor_status.fuel_flow
                if sensor_status is not None
                else None
            ),
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "FUEL REM",
            engine.fuel_remaining_gal,
            "GAL",
            fuel_color,
            decimals=1,
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "FUEL USED",
            engine.fuel_used_gal,
            "GAL",
            QColor(255, 255, 255),
            decimals=1,
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "ENDURANCE",
            engine.endurance_hr,
            "HR",
            fuel_color,
            decimals=1,
        )
        y += 35

        self.draw_value(
            painter,
            40,
            y,
            "RANGE",
            engine.fuel_range_nm,
            "NM",
            fuel_color,
            decimals=0,
        )
        self.draw_cht_column(
            painter,
            engine,
            x=390,
            y=105,
            statuses=(
                sensor_status.cht
                if sensor_status is not None
                else None
            ),
        )
        self.draw_egt_column(
            painter,
            engine,
            x=620,
            y=105,
            statuses=(
                sensor_status.egt
                if sensor_status is not None
                else None
            ),
        )
        self.draw_status_indicators(
            painter,
            engine,
            width,
            height,
            sensor_status=sensor_status,
        )

        self.draw_cylinder_analysis_box(
            painter,
            cylinders,
            width,
            height,
        )

        if checklist is not None:
            self.draw_checklist_status(
                painter,
                checklist,
                width,
                height,
            )

        if aircraft is not None:
            self.draw_aircraft_state_label(
                painter,
                aircraft,
                width,
                height,
            )
            
        if engine_advice is not None:
            self.draw_engine_advice_box(
                painter,
                engine_advice,
                width,
                height,
            )
            
        if aircraft_recommendation is not None:
            self.draw_aircraft_recommendation_box(
            painter,
            aircraft_recommendation,
            width,
            height,
        )
            
        if engine_state is not None:
            self.draw_engine_health_box(painter, engine_state.health, width, height)
            self.draw_engine_analysis_box(painter, engine_state.analysis, width, height)
            self.draw_engine_trend_box(painter, engine_state.trend, width, height)
    def draw_value(
        self,
        painter: QPainter,
        x: int,
        y: int,
        label: str,
        value: float,
        unit: str,
        color: QColor,
        decimals: int = 0,
        signed: bool = False,
        status=None,
    ) -> None:
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(x, y, f"{label:<12}")

        if (
            status is not None
            and (
                not status.valid
                or not status.fresh
            )
        ):
            painter.setPen(QColor(255, 80, 80))
            painter.drawText(
                x + 155,
                y,
                f"--- {unit}",
            )
            return

        painter.setPen(color)

        if signed:
            text = f"{value:+.{decimals}f}"
        else:
            text = f"{value:.{decimals}f}"

        painter.drawText(
            x + 155,
            y,
            f"{text} {unit}",
        )

    def draw_bar(
        self,
        painter: QPainter,
        x: int,
        y: int,
        label: str,
        value: float,
        min_value: float,
        max_value: float,
        color: QColor,
        unit: str = "°F",
    ) -> None:
        bar_w = 130
        bar_h = 16

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(x, y, label)

        painter.setPen(QPen(QColor(90, 90, 90), 1))
        painter.drawRect(x + 65, y - 14, bar_w, bar_h)

        ratio = (value - min_value) / (max_value - min_value)
        ratio = max(0.0, min(1.0, ratio))

        fill_w = int(bar_w * ratio)

        painter.fillRect(x + 66, y - 13, fill_w, bar_h - 2, color)

        painter.setPen(color)
        painter.drawText(x + 210, y, f"{value:.0f}{unit}")

    def draw_cht_column(
        self,
        painter: QPainter,
        engine: EngineData,
        x: int,
        y: int,
        statuses=None,
    ) -> None:
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(x, y, "CHT")

        y += 35

        for index, cht in enumerate(engine.cht_f, start=1):
            status = (
                statuses[index - 1]
                if (
                    statuses is not None
                    and index - 1 < len(statuses)
                )
                else None
            )

            if (
                status is not None
                and (
                    not status.valid
                    or not status.fresh
                )
            ):
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(
                    x,
                    y,
                    f"CHT{index}",
                )

                painter.setPen(QColor(255, 80, 80))
                painter.drawText(
                    x + 210,
                    y,
                    "---°F",
                )

                y += 32
                continue

            self.draw_bar(
                painter=painter,
                x=x,
                y=y,
                label=f"CHT{index}",
                value=cht,
                min_value=200,
                max_value=500,
                color=self.cht_color(cht),
            )
            y += 32

    def draw_egt_column(
        self,
        painter: QPainter,
        engine: EngineData,
        x: int,
        y: int,
        statuses=None,
    ) -> None:
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(x, y, "EGT")

        y += 35

        for index, egt in enumerate(engine.egt_f, start=1):
            status = (
                statuses[index - 1]
                if (
                    statuses is not None
                    and index - 1 < len(statuses)
                )
                else None
            )

            if (
                status is not None
                and (
                    not status.valid
                    or not status.fresh
                )
            ):
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(
                    x,
                    y,
                    f"EGT{index}",
                )

                painter.setPen(QColor(255, 80, 80))
                painter.drawText(
                    x + 210,
                    y,
                    "---°F",
                )

                y += 32
                continue

            self.draw_bar(
                painter=painter,
                x=x,
                y=y,
                label=f"EGT{index}",
                value=egt,
                min_value=1000,
                max_value=1650,
                color=self.egt_color(egt),
            )
            y += 32

    def draw_status_indicators(
        self,
        painter: QPainter,
        engine: EngineData,
        width: int,
        height: int,
        sensor_status=None,
    ) -> None:
        x = width - 220
        y = height - 170

        painter.setFont(QFont("Arial", 15, QFont.Weight.Bold))

        self.draw_status(painter, x, y, "IGN A", engine.ignition_a)
        y += 35

        self.draw_status(painter, x, y, "IGN B", engine.ignition_b)
        y += 35

        electrical_usable = (
            sensor_status is None
            or (
                sensor_status.volts.valid
                and sensor_status.volts.fresh
                and sensor_status.amps.valid
                and sensor_status.amps.fresh
            )
        )

        if electrical_usable:
            self.draw_status(
                painter,
                x,
                y,
                "ALT",
                engine.alternator_online,
            )
        else:
            painter.setPen(QColor(255, 220, 0))
            painter.drawText(
                x,
                y,
                "ALT ---",
            )

        y += 35

        starter_color = (
            QColor(255, 220, 0)
            if engine.starter_engaged
            else QColor(255, 255, 255)
        )
        painter.setPen(starter_color)
        painter.drawText(x, y, f"START {'ON' if engine.starter_engaged else 'OFF'}")

    def draw_status(
        self,
        painter: QPainter,
        x: int,
        y: int,
        label: str,
        ok: bool,
    ) -> None:
        painter.setPen(QColor(0, 255, 0) if ok else QColor(255, 0, 0))
        painter.drawText(x, y, f"{label} {'ON' if ok else 'OFF'}")

    def draw_annunciators(
        self,
        painter: QPainter,
        engine: EngineData,
        width: int,
        sensor_status=None,
    ) -> None:
        config = load_config()
        fuel = config.fuel

        annunciators: list[tuple[str, QColor]] = []

        def channel_usable(status) -> bool:
            return (
                status is None
                or (
                    status.valid
                    and status.fresh
                )
            )

        rpm_status = (
            sensor_status.rpm
            if sensor_status is not None
            else None
        )
        oil_pressure_status = (
            sensor_status.oil_pressure
            if sensor_status is not None
            else None
        )
        oil_temperature_status = (
            sensor_status.oil_temperature
            if sensor_status is not None
            else None
        )
        volts_status = (
            sensor_status.volts
            if sensor_status is not None
            else None
        )

        amps_status = (
            sensor_status.amps
            if sensor_status is not None
            else None
        )

        electrical_usable = (
            channel_usable(volts_status)
            and channel_usable(amps_status)
        )

        if (
            channel_usable(rpm_status)
            and channel_usable(oil_pressure_status)
            and engine.rpm > 2000
            and engine.oil_pressure_psi < 20
        ):
            annunciators.append(
                ("LOW OIL PRESS", QColor(255, 0, 0))
            )

        if (
            channel_usable(oil_pressure_status)
            and engine.oil_pressure_psi <= 15
        ):
            annunciators.append(
                ("OIL PRESS", QColor(255, 0, 0))
            )

        if (
            channel_usable(oil_temperature_status)
            and engine.oil_temp_f >= 260
        ):
            annunciators.append(
                ("HIGH OIL TEMP", QColor(255, 0, 0))
            )
        elif (
            channel_usable(oil_temperature_status)
            and engine.oil_temp_f >= 235
        ):
            annunciators.append(
                ("OIL TEMP", QColor(255, 220, 0))
            )

        if (
            channel_usable(volts_status)
            and (
                engine.volts < 12.0
                or engine.volts > 16.0
            )
        ):
            annunciators.append(
                ("VOLTS", QColor(255, 0, 0))
            )
        elif (
            channel_usable(volts_status)
            and (
                engine.volts < 13.2
                or engine.volts > 15.5
            )
        ):
            annunciators.append(
                ("VOLTS", QColor(255, 220, 0))
            )

        usable_cht_values = [
            value
            for index, value in enumerate(
                engine.cht_f
            )
            if (
                sensor_status is None
                or (
                    index < len(sensor_status.cht)
                    and channel_usable(
                        sensor_status.cht[index]
                    )
                )
            )
        ]

        if (
            usable_cht_values
            and max(usable_cht_values) >= 450
        ):
            annunciators.append(
                ("HIGH CHT", QColor(255, 0, 0))
            )
        elif (
            usable_cht_values
            and max(usable_cht_values) >= 425
        ):
            annunciators.append(
                ("CHT", QColor(255, 220, 0))
            )

        usable_egt_values = [
            value
            for index, value in enumerate(
                engine.egt_f
            )
            if (
                sensor_status is None
                or (
                    index < len(sensor_status.egt)
                    and channel_usable(
                        sensor_status.egt[index]
                    )
                )
            )
        ]

        if (
            usable_egt_values
            and max(usable_egt_values) >= 1600
        ):
            annunciators.append(
                ("HIGH EGT", QColor(255, 0, 0))
            )

        if (
            channel_usable(rpm_status)
            and engine.rpm > 3500
        ):
            annunciators.append(
                ("RPM", QColor(255, 0, 0))
            )

        if (
            electrical_usable
            and not engine.alternator_online
        ):
            annunciators.append(
                ("ALT FAIL", QColor(255, 0, 0))
            )

        if not engine.ignition_a:
            annunciators.append(("IGN A OFF", QColor(255, 0, 0)))

        if not engine.ignition_b:
            annunciators.append(("IGN B OFF", QColor(255, 0, 0)))

        if engine.starter_engaged:
            annunciators.append(("START", QColor(255, 220, 0)))
        
        if engine.fuel_remaining_gal <= fuel.red_gal:
            annunciators.append(("LOW FUEL", QColor(255, 0, 0)))
        elif engine.fuel_remaining_gal <= fuel.yellow_gal:
            annunciators.append(("FUEL", QColor(255, 220, 0)))

        if engine.endurance_hr <= fuel.red_endurance_hr:
            annunciators.append(("LOW ENDURANCE", QColor(255, 0, 0)))
        elif engine.endurance_hr <= fuel.yellow_endurance_hr:
            annunciators.append(("ENDURANCE", QColor(255, 220, 0)))

        if not annunciators:
            annunciators.append(("ENGINE NORMAL", QColor(0, 255, 0)))

        x = 20
        y = 62
        box_w = 150
        box_h = 28

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        for text, color in annunciators[:6]:
            painter.fillRect(x, y, box_w, box_h, color)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(
                QRectF(x, y, box_w, box_h),
                Qt.AlignmentFlag.AlignCenter,
                text,
            )
            x += box_w + 10

    

    def fuel_color(self, engine: EngineData) -> QColor:
        config = load_config()
        fuel = config.fuel

        if engine.fuel_remaining_gal <= fuel.red_gal:
            return QColor(255, 0, 0)

        if engine.fuel_remaining_gal <= fuel.yellow_gal:
            return QColor(255, 220, 0)

        if engine.endurance_hr <= fuel.red_endurance_hr:
            return QColor(255, 0, 0)

        if engine.endurance_hr <= fuel.yellow_endurance_hr:
            return QColor(255, 220, 0)

        return QColor(0, 255, 0)

    def rpm_color(self, rpm: float) -> QColor:
        if rpm > 3500:
            return QColor(255, 0, 0)

        return QColor(0, 255, 0)

    def cht_color(self, value: float) -> QColor:
        if value >= 450:
            return QColor(255, 0, 0)

        if value >= 425:
            return QColor(255, 220, 0)

        return QColor(0, 255, 0)

    def egt_color(self, value: float) -> QColor:
        if value >= 1600:
            return QColor(255, 0, 0)

        return QColor(0, 255, 0)

    def oil_temp_color(self, value: float) -> QColor:
        if value >= 260:
            return QColor(255, 0, 0)

        if value >= 235:
            return QColor(255, 220, 0)

        return QColor(0, 255, 0)

    def oil_pressure_color(self, pressure: float, rpm: float) -> QColor:
        if pressure <= 15:
            return QColor(255, 0, 0)

        if rpm > 2000 and pressure < 20:
            return QColor(255, 0, 0)

        if pressure >= 50:
            return QColor(255, 220, 0)

        if pressure < 20:
            return QColor(255, 220, 0)

        return QColor(0, 255, 0)

    def voltage_color(self, volts: float) -> QColor:
        if volts < 12.0 or volts > 16.0:
            return QColor(255, 0, 0)

        if volts < 13.2 or volts > 15.5:
            return QColor(255, 220, 0)

        return QColor(0, 255, 0)

    def draw_test_mode_label(self, painter: QPainter, width: int) -> None:
        config = load_config()
        ems_test = getattr(
            config,
            "ems_test",
            None,
        )
        mode = getattr(
            ems_test,
            "mode",
            "normal",
        )

        if mode == "normal":
            return

        box_w = 260
        box_h = 28
        box_x = width - box_w - 20
        box_y = 62

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(255, 120, 0))
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(
            QRectF(box_x, box_y, box_w, box_h),
            Qt.AlignmentFlag.AlignCenter,
            f"EMS TEST: {mode.upper()}",
        )
    def draw_checklist_status(self, painter: QPainter, checklist, width: int, height: int) -> None:
        box_x = 40
        box_y = height - 90
        box_w = 420
        box_h = 42

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 18, "CHECKLIST")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            box_x + 120,
            box_y + 18,
            checklist.progress_summary(),
        )

        painter.drawText(
            box_x + 120,
            box_y + 36,
            checklist.all_phases_summary(),
        )
        
    def draw_aircraft_state_label(self, painter: QPainter, aircraft, width: int, height: int) -> None:
        phase = getattr(aircraft, "phase", "UNKNOWN")
        moving = "MOVING" if getattr(aircraft, "aircraft_moving", False) else "STOPPED"
        airborne = "AIRBORNE" if getattr(aircraft, "airborne", False) else "GROUND"

        box_x = width - 280
        box_y = height - 90
        box_w = 240
        box_h = 42

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 17, f"PHASE: {phase}")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 35, f"{moving} / {airborne}")
        
    def draw_engine_health_box(self, painter: QPainter, engine_health, width: int, height: int) -> None:
        box_x = width - 280
        box_y = height - 145
        box_w = 240
        box_h = 48

        score = getattr(engine_health, "health_score", 100)
        status = getattr(engine_health, "status", "NORMAL")

        if score >= 85:
            color = QColor(0, 255, 0)
        elif score >= 60:
            color = QColor(255, 220, 0)
        else:
            color = QColor(255, 0, 0)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 20, f"ENGINE HEALTH: {score}%")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 40, f"STATUS: {status}")
    
    def draw_engine_analysis_box(self, painter: QPainter, engine_analysis, width: int, height: int) -> None:
        box_x = 40
        box_y = height - 145
        box_w = 520
        box_h = 48

        severity = getattr(engine_analysis, "severity", "NORMAL")
        summary = getattr(engine_analysis, "summary", "")
        recommendation = getattr(engine_analysis, "recommendation", "")

        color = QColor(0, 255, 0)
        if severity == "CAUTION":
            color = QColor(255, 220, 0)
        elif severity in {"WARNING", "CRITICAL"}:
            color = QColor(255, 0, 0)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 18, f"ENGINE ANALYSIS: {severity}")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 35, summary[:55])
        
    def draw_engine_trend_box(self, painter: QPainter, engine_trend, width: int, height: int) -> None:
        box_x = 580
        box_y = height - 145
        box_w = 300
        box_h = 48

        predicted_cht = getattr(engine_trend, "predicted_cht", 0.0)
        predicted_oil_temp = getattr(engine_trend, "predicted_oil_temp", 0.0)
        warning = getattr(engine_trend, "warning", "")

        color = QColor(0, 255, 0)
        if warning:
            color = QColor(255, 220, 0)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 18, "ENGINE TREND")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            box_x + 10,
            box_y + 35,
            f"30s CHT {predicted_cht:.0f}F  OIL {predicted_oil_temp:.0f}F",
        )
        
    def draw_cylinder_analysis_box(self, painter: QPainter, cylinders, width: int, height: int) -> None:
        box_x = 900
        box_y = height - 145
        box_w = 300
        box_h = 48

        imbalance = getattr(cylinders, "imbalance_detected", False)
        message = getattr(cylinders, "message", "Cylinders balanced.")

        color = QColor(255, 220, 0) if imbalance else QColor(0, 255, 0)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 18, "CYLINDER BALANCE")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 35, message[:38])
        
    def draw_engine_advice_box(
        self,
        painter: QPainter,
        advice,
        width: int,
        height: int,
    ) -> None:
        severity = getattr(advice, "severity", "NORMAL")

        if severity == "NORMAL":
            return

        title = getattr(
            advice,
            "title",
            "Engine Advisor",
        )

        reason = getattr(
            advice,
            "reason",
            "Engine advisory condition detected.",
        )

        action = getattr(
            advice,
            "action",
            "Monitor engine instruments.",
        )

        confidence = getattr(
            advice,
            "confidence",
            0.0,
        )

        box_x = 40
        box_y = height - 270
        box_w = width - 80
        box_h = 58

        color = QColor(255, 220, 0)
        if severity in {"WARNING", "CRITICAL"}:
            color = QColor(255, 0, 0)

        painter.fillRect(
            box_x,
            box_y,
            box_w,
            box_h,
            QColor(0, 0, 0),
        )

        painter.setPen(QPen(color, 2))
        painter.drawRect(
            box_x,
            box_y,
            box_w,
            box_h,
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Weight.Bold,
            )
        )
        painter.setPen(color)

        painter.drawText(
            box_x + 10,
            box_y + 18,
            (
                f"ENGINE ADVISOR: {title} "
                f"[{severity}] "
                f"CONF {confidence * 100:.0f}%"
            ),
        )

        painter.setFont(
            QFont(
                "Arial",
                9,
                QFont.Weight.Bold,
            )
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        painter.drawText(
            box_x + 10,
            box_y + 36,
            f"WHY: {reason[:70]}",
        )

        painter.drawText(
            box_x + 10,
            box_y + 52,
            f"ACTION: {action[:70]}",
        )
        
    def draw_aircraft_recommendation_box(
        self,
        painter: QPainter,
        recommendation,
        width: int,
        height: int,
    ) -> None:
        box_x = 40
        box_y = height - 205
        box_w = width - 80
        box_h = 50

        severity = getattr(recommendation, "severity", "NORMAL")
        title = getattr(recommendation, "title", "Normal")
        message = getattr(recommendation, "message", "Aircraft systems normal.")
        action = getattr(recommendation, "recommendation", "Continue normal operation.")
        
        urgency_s = getattr(recommendation, "urgency_s", None)

        urgency_text = ""
        if urgency_s is not None:
            urgency_text = f"  LIMIT IN {urgency_s:.0f}s"
            
        confidence = getattr(recommendation, "confidence", None)
        confidence_text = ""
        if confidence is not None:
            confidence_text = f"  CONF {confidence * 100:.0f}%"

        color = QColor(0, 255, 0)
        if severity == "CAUTION":
            color = QColor(255, 220, 0)
        elif severity in {"WARNING", "CRITICAL"}:
            color = QColor(255, 0, 0)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(
            box_x + 10,
            box_y + 20,
            f"AI RECOMMENDATION: {title} [{severity}]{urgency_text}{confidence_text}",
        )

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 40, f"{message[:55]}  ACTION: {action[:55]}")