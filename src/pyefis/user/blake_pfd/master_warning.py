from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter
from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.engine_data import EngineData


@dataclass
class WarningItem:
    text: str
    color: QColor

def format_ai_warning_text(
    title: str,
    urgency_s: float | None = None,
    confidence: float | None = None,
    max_title_length: int = 22,
) -> str:
    clean_title = str(title).strip().upper()

    if len(clean_title) > max_title_length:
        clean_title = (
            clean_title[: max_title_length - 1]
            + "…"
        )

    parts = [
        "AI",
        clean_title,
    ]

    if urgency_s is not None:
        safe_urgency_s = max(
            0.0,
            float(urgency_s),
        )

        parts.append(
            f"{safe_urgency_s:.0f}s"
        )

    if confidence is not None:
        safe_confidence = min(
            1.0,
            max(
                0.0,
                float(confidence),
            ),
        )

        parts.append(
            f"{safe_confidence * 100:.0f}%"
        )

    return " ".join(
        part
        for part in parts
        if part
    )


def get_engine_warnings(
    engine: EngineData,
    sensor_status=None,
) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    config = load_config()
    fuel = config.fuel

    def channel_usable(status) -> bool:
        return (
            status is None
            or (
                status.valid
                and status.fresh
            )
        )

    rpm_usable = (
        sensor_status is None
        or channel_usable(sensor_status.rpm)
    )

    volts_usable = (
        sensor_status is None
        or channel_usable(sensor_status.volts)
    )

    oil_pressure_usable = (
        sensor_status is None
        or channel_usable(sensor_status.oil_pressure)
    )

    oil_temperature_usable = (
        sensor_status is None
        or channel_usable(sensor_status.oil_temperature)
    )

    valid_cht_values = [
        value
        for index, value in enumerate(engine.cht_f or [])
        if (
            sensor_status is None
            or (
                index < len(sensor_status.cht)
                and channel_usable(sensor_status.cht[index])
            )
        )
    ]

    valid_egt_values = [
        value
        for index, value in enumerate(engine.egt_f or [])
        if (
            sensor_status is None
            or (
                index < len(sensor_status.egt)
                and channel_usable(sensor_status.egt[index])
            )
        )
    ]

    if (
        rpm_usable
        and oil_pressure_usable
        and engine.rpm > 2000
        and engine.oil_pressure_psi < 20
    ):
        warnings.append(WarningItem("LOW OIL PRESS", QColor(255, 0, 0)))

    if (
        oil_pressure_usable
        and engine.oil_pressure_psi <= 15
    ):
        warnings.append(WarningItem("OIL PRESS", QColor(255, 0, 0)))

    if (
        oil_temperature_usable
        and engine.oil_temp_f >= 260
    ):
        warnings.append(WarningItem("HIGH OIL TEMP", QColor(255, 0, 0)))
    elif (
        oil_temperature_usable
        and engine.oil_temp_f >= 235
    ):
        warnings.append(WarningItem("OIL TEMP", QColor(255, 220, 0)))

    if valid_cht_values and max(valid_cht_values) >= 450:
        warnings.append(WarningItem("HIGH CHT", QColor(255, 0, 0)))
    elif valid_cht_values and max(valid_cht_values) >= 425:
        warnings.append(WarningItem("CHT", QColor(255, 220, 0)))

    if valid_egt_values and max(valid_egt_values) >= 1600:
        warnings.append(WarningItem("HIGH EGT", QColor(255, 0, 0)))

    if rpm_usable and engine.rpm > 3500:
        warnings.append(WarningItem("RPM", QColor(255, 0, 0)))

    if (
        volts_usable
        and (
            engine.volts < 12.0
            or engine.volts > 16.0
        )
    ):
        warnings.append(WarningItem("VOLTS", QColor(255, 0, 0)))
    elif (
        volts_usable
        and (
            engine.volts < 13.2
            or engine.volts > 15.5
        )
    ):
        warnings.append(WarningItem("VOLTS", QColor(255, 220, 0)))

    if not engine.alternator_online:
        warnings.append(WarningItem("ALT FAIL", QColor(255, 0, 0)))

    if not engine.ignition_a:
        warnings.append(WarningItem("IGN A OFF", QColor(255, 0, 0)))

    if not engine.ignition_b:
        warnings.append(WarningItem("IGN B OFF", QColor(255, 0, 0)))

    if engine.starter_engaged:
        warnings.append(WarningItem("START", QColor(255, 220, 0)))

    if engine.fuel_remaining_gal <= fuel.red_gal:
        warnings.append(WarningItem("LOW FUEL", QColor(255, 0, 0)))
    elif engine.fuel_remaining_gal <= fuel.yellow_gal:
        warnings.append(WarningItem("FUEL", QColor(255, 220, 0)))

    if engine.endurance_hr <= fuel.red_endurance_hr:
        warnings.append(WarningItem("LOW ENDURANCE", QColor(255, 0, 0)))
    elif engine.endurance_hr <= fuel.yellow_endurance_hr:
        warnings.append(WarningItem("ENDURANCE", QColor(255, 220, 0)))

    return warnings


def get_checklist_warnings(
    checklist=None,
    aircraft_moving: bool = False,
    flight_phase: str = "PARKED",
) -> list[WarningItem]:
    warnings: list[WarningItem] = []

    if checklist is None:
        return warnings

    warning_phases = {
        "RUNUP",
        "TAKEOFF",
        "CLIMB",
        "DESCENT",
        "LANDING",
    }

    if flight_phase not in warning_phases:
        return warnings

    if not aircraft_moving and flight_phase != "RUNUP":
        return warnings

    if not checklist.active_phase_complete():
        warnings.append(WarningItem("CHECKLIST", QColor(255, 220, 0)))

    return warnings


def draw_master_warning_strip(
    painter: QPainter,
    engine: EngineData,
    width: int,
    checklist=None,
    aircraft_moving: bool = False,
    aircraft_recommendation=None,
    sensor_status=None,
) -> None:
    if sensor_status is None:
        warnings = get_engine_warnings(
            engine,
        )
    else:
        warnings = get_engine_warnings(
            engine,
            sensor_status=sensor_status,
        )
    warnings.extend(
        get_checklist_warnings(
            checklist=checklist,
            aircraft_moving=aircraft_moving,
            flight_phase=getattr(checklist, "current_phase_name", lambda: "PARKED")(),
        )
    )

    if aircraft_recommendation is not None:
        severity = getattr(aircraft_recommendation, "severity", "NORMAL")
        title = getattr(aircraft_recommendation, "title", "")
        warning_text = format_ai_warning_text(
            title=title,
            urgency_s=getattr(
                aircraft_recommendation,
                "urgency_s",
                None,
            ),
            confidence=getattr(
                aircraft_recommendation,
                "confidence",
                None,
            ),
        )

        if severity in {"WARNING", "CRITICAL"}:
            warnings.append(
                WarningItem(
                    warning_text,
                    QColor(255, 0, 0),
                )
            )
        elif severity == "CAUTION":
            warnings.append(
                WarningItem(
                    warning_text,
                    QColor(255, 220, 0),
                )
            )

    if not warnings:
        warnings.append(WarningItem("ENGINE NORMAL", QColor(0, 255, 0)))

    x = 10
    y = 5
    box_w = 150
    box_h = 28

    painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))

    for warning in warnings[:6]:
        painter.fillRect(x, y, box_w, box_h, warning.color)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(
            QRectF(x, y, box_w, box_h),
            Qt.AlignmentFlag.AlignCenter,
            warning.text,
        )
        x += box_w + 8

    config = load_config()
    mode = getattr(config.ems_test, "mode", "normal")

    if mode != "normal":
        test_box_w = 210
        test_box_h = 28
        test_x = width - test_box_w - 10
        test_y = 5

        painter.fillRect(test_x, test_y, test_box_w, test_box_h, QColor(255, 120, 0))
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(
            QRectF(test_x, test_y, test_box_w, test_box_h),
            Qt.AlignmentFlag.AlignCenter,
            f"TEST: {mode.upper()}",
        )