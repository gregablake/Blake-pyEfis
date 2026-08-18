from __future__ import annotations

import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


def test_pfd_demo_constructs(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    try:
        assert widget is not None
        assert widget.config is not None
        assert widget.page_manager is not None
        assert widget.direct_to_guidance is not None
        assert (
            widget.direct_to_lateral_guidance
            is not None
        )
    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()


def test_pfd_demo_renders_offscreen(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.resize(
        1280,
        720,
    )

    image = QImage(
        1280,
        720,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.update_data()

        widget.render(
            painter,
        )

        assert image.isNull() is False
    finally:
        painter.end()

        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()
        
def test_pfd_demo_renders_sensor_failure_banner(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    widget.resize(
        1280,
        720,
    )

    image = QImage(
        1280,
        720,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.update_data()

        widget.sensor_watchdog_state = (
            widget.sensor_watchdog.evaluate(
                flight_data_available=True,
                position_valid=False,
                attitude_valid=False,
                air_data_valid=False,
            )
        )

        assert (
            widget.sensor_watchdog_state.degraded
            is True
        )

        assert (
            widget.sensor_watchdog_state.message
            == "DEGRADED: ATTITUDE / AIR DATA / GPS"
        )

        widget.render(
            painter,
        )

        assert image.isNull() is False

    finally:
        painter.end()

        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()
        
def test_pfd_demo_sensor_fault_message(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    try:
        widget.sensor_fault_message = (
            "AHRS DATA STALE"
        )

        assert (
            widget.sensor_fault_message
            == "AHRS DATA STALE"
        )

        widget.sensor_fault_message = (
            "AHRS DATA STALE / GPS FAIL"
        )

        assert (
            widget.sensor_fault_message
            == "AHRS DATA STALE / GPS FAIL"
        )

    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()
        
def test_pfd_demo_renders_startup_blocked_banner(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    widget.resize(
        1280,
        720,
    )

    image = QImage(
        1280,
        720,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.update_data()

        widget.startup_gate_state = (
            widget.startup_gate.evaluate(
                config_ok=False,
                database_ok=True,
                flight_data_available=True,
                attitude_valid=True,
                air_data_valid=True,
                hardware_mode=False,
            )
        )

        assert widget.startup_gate_state.blocked is True
        assert (
            widget.startup_gate_state.message
            == "STARTUP BLOCKED: CONFIG"
        )

        widget.render(
            painter,
        )

        assert image.isNull() is False

    finally:
        painter.end()

        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()


def test_pfd_demo_renders_startup_initializing_banner(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    widget.resize(
        1280,
        720,
    )

    image = QImage(
        1280,
        720,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.update_data()

        widget.startup_gate_state = (
            widget.startup_gate.evaluate(
                config_ok=True,
                database_ok=True,
                flight_data_available=True,
                attitude_valid=False,
                air_data_valid=False,
                hardware_mode=True,
            )
        )

        assert widget.startup_gate_state.initializing is True
        assert (
            widget.startup_gate_state.message
            == "INITIALIZING: AHRS / AIR DATA"
        )

        widget.render(
            painter,
        )

        assert image.isNull() is False

    finally:
        painter.end()

        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()
        
def test_pfd_demo_renders_unclean_restart_banner(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    widget.resize(
        1280,
        720,
    )

    image = QImage(
        1280,
        720,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.update_data()

        widget.reboot_recovery_state = (
            widget.reboot_recovery.evaluate(
                previous_shutdown_clean=False,
                startup_ready=False,
                flight_data_valid=False,
            )
        )

        assert (
            widget.reboot_recovery_state
            .recovery_required
            is True
        )

        assert (
            widget.reboot_recovery_state
            .inhibit_ready
            is True
        )

        assert (
            widget.reboot_recovery_state.message
            == (
                "UNCLEAN RESTART - "
                "WAITING FOR FLIGHT DATA"
            )
        )

        widget.render(
            painter,
        )

        assert image.isNull() is False

    finally:
        painter.end()

        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()
        