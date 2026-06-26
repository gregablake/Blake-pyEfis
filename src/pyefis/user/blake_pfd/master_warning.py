from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter

from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.config_loader import load_config


@dataclass
class WarningItem:
    text: str
    color: QColor


def get_engine_warnings(engine: EngineData) -> list[WarningItem]:
    warnings: list[WarningItem] = []

    if engine.rpm > 2000 and engine.oil_pressure_psi < 20:
        warnings.append(WarningItem("LOW OIL PRESS", QColor(255, 0, 0)))

    if engine.oil_temp_f >= 260:
        warnings.append(WarningItem("HIGH OIL TEMP", QColor(255, 0, 0)))
    elif engine.oil_temp_f >= 235:
        warnings.append(WarningItem("OIL TEMP", QColor(255, 220, 0)))

    if max(engine.cht_f or [0.0]) >= 450:
        warnings.append(WarningItem("HIGH CHT", QColor(255, 0, 0)))
    elif max(engine.cht_f or [0.0]) >= 425:
        warnings.append(WarningItem("CHT", QColor(255, 220, 0)))

    if max(engine.egt_f or [0.0]) >= 1600:
        warnings.append(WarningItem("HIGH EGT", QColor(255, 0, 0)))

    if engine.volts < 12.0 or engine.volts > 16.0:
        warnings.append(WarningItem("VOLTS", QColor(255, 0, 0)))
    elif engine.volts < 13.2 or engine.volts > 15.5:
        warnings.append(WarningItem("VOLTS", QColor(255, 220, 0)))

    if not engine.alternator_online:
        warnings.append(WarningItem("ALT FAIL", QColor(255, 0, 0)))

    if not engine.ignition_a:
        warnings.append(WarningItem("IGN A OFF", QColor(255, 0, 0)))

    if not engine.ignition_b:
        warnings.append(WarningItem("IGN B OFF", QColor(255, 0, 0)))

    if engine.starter_engaged:
        warnings.append(WarningItem("START", QColor(255, 220, 0)))

    if not warnings:
        warnings.append(WarningItem("ENGINE NORMAL", QColor(0, 255, 0)))

    return warnings


def draw_master_warning_strip(
    painter: QPainter,
    engine: EngineData,
    width: int,
) -> None:
    warnings = get_engine_warnings(engine)

    x = 10
    y = 5
    box_w = 150
    box_h = 28

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