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

def test_transient_ai_caution_does_not_reach_display(
    qapp: QApplication,
) -> None:
    class Recommendation:
        def __init__(
            self,
            severity: str,
            title: str,
            message: str,
        ) -> None:
            self.severity = severity
            self.title = title
            self.message = message
            self.recommendation = "Monitor."
            self.urgency_s = None
            self.confidence = None
            self.source_priority = 0

    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    try:
        sequence = iter(
            [
                Recommendation(
                    "CAUTION",
                    "Engine Caution",
                    "Transient condition.",
                ),
                Recommendation(
                    "NORMAL",
                    "Normal",
                    "Aircraft systems normal.",
                ),
            ]
        )

        widget.aircraft_intelligence.analyze = (
            lambda aircraft: next(sequence)
        )

        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "NORMAL"
        )

        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "NORMAL"
        )

    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()

def test_sustained_ai_caution_reaches_display_after_latch(
    qapp: QApplication,
) -> None:
    class Recommendation:
        def __init__(
            self,
            severity: str,
            title: str,
            message: str,
        ) -> None:
            self.severity = severity
            self.title = title
            self.message = message
            self.recommendation = "Monitor."
            self.urgency_s = None
            self.confidence = None
            self.source_priority = 0

    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    try:
        caution = Recommendation(
            "CAUTION",
            "Engine Caution",
            "Persistent condition.",
        )

        widget.aircraft_intelligence.analyze = (
            lambda aircraft: caution
        )

        widget.update_data()
        assert (
            widget.aircraft_recommendation.severity
            == "NORMAL"
        )

        widget.update_data()
        assert (
            widget.aircraft_recommendation.severity
            == "NORMAL"
        )

        widget.update_data()
        assert (
            widget.aircraft_recommendation.severity
            == "CAUTION"
        )

        assert (
            widget.aircraft_recommendation.title
            == "Engine Caution"
        )

    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()

def test_latched_caution_clears_after_required_normal_samples(
    qapp: QApplication,
) -> None:
    class Recommendation:
        def __init__(
            self,
            severity: str,
            title: str,
            message: str,
        ) -> None:
            self.severity = severity
            self.title = title
            self.message = message
            self.recommendation = "Monitor."
            self.urgency_s = None
            self.confidence = None
            self.source_priority = 0

    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    try:
        caution = Recommendation(
            "CAUTION",
            "Engine Caution",
            "Persistent condition.",
        )

        normal = Recommendation(
            "NORMAL",
            "Normal",
            "Aircraft systems normal.",
        )

        sequence = iter(
            [
                caution,
                caution,
                caution,
                normal,
                normal,
                normal,
                normal,
                normal,
            ]
        )

        widget.aircraft_intelligence.analyze = (
            lambda aircraft: next(sequence)
        )

        # Latch the caution.
        widget.update_data()
        widget.update_data()
        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "CAUTION"
        )

        # Four clear samples are not enough.
        widget.update_data()
        widget.update_data()
        widget.update_data()
        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "CAUTION"
        )

        # Fifth clear sample releases the latch.
        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "NORMAL"
        )

        assert (
            widget.aircraft_recommendation.title
            == "Normal"
        )

    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()

def test_critical_immediately_replaces_latched_caution(
    qapp: QApplication,
) -> None:
    class Recommendation:
        def __init__(
            self,
            severity: str,
            title: str,
            message: str,
        ) -> None:
            self.severity = severity
            self.title = title
            self.message = message
            self.recommendation = "Take action."
            self.urgency_s = None
            self.confidence = None
            self.source_priority = 0

    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    try:
        caution = Recommendation(
            "CAUTION",
            "Engine Caution",
            "Persistent caution.",
        )

        critical = Recommendation(
            "CRITICAL",
            "Oil Pressure",
            "Oil pressure critically low.",
        )

        sequence = iter(
            [
                caution,
                caution,
                caution,
                critical,
            ]
        )

        widget.aircraft_intelligence.analyze = (
            lambda aircraft: next(sequence)
        )

        widget.update_data()
        widget.update_data()
        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "CAUTION"
        )

        # Higher severity must replace the caution
        # on the very next sample.
        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "CRITICAL"
        )

        assert (
            widget.aircraft_recommendation.title
            == "Oil Pressure"
        )

    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()

def test_latched_caution_survives_brief_clear(
    qapp: QApplication,
) -> None:
    class Recommendation:
        def __init__(
            self,
            severity: str,
            title: str,
            message: str,
        ) -> None:
            self.severity = severity
            self.title = title
            self.message = message
            self.recommendation = "Monitor."
            self.urgency_s = None
            self.confidence = None
            self.source_priority = 0

    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    try:
        caution = Recommendation(
            "CAUTION",
            "Engine Caution",
            "Persistent condition.",
        )

        normal = Recommendation(
            "NORMAL",
            "Normal",
            "Aircraft systems normal.",
        )

        sequence = iter(
            [
                caution,
                caution,
                caution,
                normal,
            ]
        )

        widget.aircraft_intelligence.analyze = (
            lambda aircraft: next(sequence)
        )

        widget.update_data()
        widget.update_data()
        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "CAUTION"
        )

        # One NORMAL sample must not clear
        # the already latched caution.
        widget.update_data()

        assert (
            widget.aircraft_recommendation.severity
            == "CAUTION"
        )

        assert (
            widget.aircraft_recommendation.title
            == "Engine Caution"
        )

    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()

def test_module_help_entrypoint_runs() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyefis.user.blake_pfd.pfd_demo",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Blake PFD visual demo" in result.stdout
    assert "--hardware" in result.stdout
    assert "--sim" in result.stdout

def test_pfd_demo_reports_stale_gps_separately(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.timer.stop()

    try:
        state = (
            widget.sensor_watchdog.evaluate(
                flight_data_available=True,
                position_valid=True,
                position_fresh=False,
                attitude_valid=True,
                air_data_valid=True,
                attitude_fresh=True,
                air_data_fresh=True,
            )
        )

        assert state.position_valid is True
        assert state.position_fresh is False
        assert state.degraded is True
        assert state.failed is False
        assert (
            state.message
            == "DEGRADED: GPS STALE"
        )

    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()

