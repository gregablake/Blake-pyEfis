from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.ems_page import EmsPage


class RecordingPainter:
    def __init__(self) -> None:
        self.text: list[str] = []

    def fillRect(self, *args) -> None:
        pass

    def setPen(self, *args) -> None:
        pass

    def setFont(self, *args) -> None:
        pass

    def drawRect(self, *args) -> None:
        pass

    def drawText(self, *args) -> None:
        if args and isinstance(args[-1], str):
            self.text.append(args[-1])
def test_ems_page_shows_unavailable_without_engine_state() -> None:
    page = EmsPage()
    painter = RecordingPainter()

    aircraft = SimpleNamespace(
        engine_state=None,
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
    )

    assert "ENGINE DATA UNAVAILABLE" in painter.text
    assert "0" not in painter.text

def test_ems_page_shows_stale_fault_message() -> None:
    page = EmsPage()
    painter = RecordingPainter()

    aircraft = SimpleNamespace(
        engine_state=None,
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        fault_message="EMS DATA STALE",
    )

    assert "EMS DATA STALE" in painter.text
    assert "ENGINE DATA UNAVAILABLE" not in painter.text

def test_ems_page_suppresses_invalid_rpm() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        rpm=9000.0,
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    sensor_status = EngineSensorStatus(
        rpm=EngineChannelStatus(
            valid=False,
            fresh=False,
            message="IMPLAUSIBLE DATA",
        )
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert "--- " in painter.text
    assert not any(
        "9000" in text
        for text in painter.text
    )

def test_bad_oil_pressure_does_not_suppress_healthy_rpm() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        rpm=2450.0,
        oil_pressure_psi=-5.0,
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    sensor_status = EngineSensorStatus(
        rpm=EngineChannelStatus(
            valid=True,
            fresh=True,
            message="DATA VALID",
        ),
        oil_pressure=EngineChannelStatus(
            valid=False,
            fresh=False,
            message="IMPLAUSIBLE DATA",
        ),
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert any(
        "2450" in text
        for text in painter.text
    )

    assert not any(
        "-5" in text
        for text in painter.text
    )

    assert any(
        "---" in text
        for text in painter.text
    )

def test_failed_cht_probe_does_not_suppress_other_cht_values() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        cht_f=[
            310.0,
            320.0,
            700.0,
            340.0,
            350.0,
            360.0,
        ],
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    failed = EngineChannelStatus(
        valid=False,
        fresh=False,
        message="IMPLAUSIBLE DATA",
    )

    sensor_status = EngineSensorStatus(
        cht=(
            healthy,
            healthy,
            failed,
            healthy,
            healthy,
            healthy,
        ),
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert any(
        "310°F" in text
        for text in painter.text
    )

    assert any(
        "320°F" in text
        for text in painter.text
    )

    assert any(
        "340°F" in text
        for text in painter.text
    )

    assert not any(
        "700°F" in text
        for text in painter.text
    )

    assert any(
        "---°F" in text
        for text in painter.text
    )

def test_failed_egt_probe_does_not_suppress_other_egt_values() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        egt_f=[
            1350.0,
            2500.0,
        ],
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    failed = EngineChannelStatus(
        valid=False,
        fresh=False,
        message="IMPLAUSIBLE DATA",
    )

    sensor_status = EngineSensorStatus(
        egt=(
            healthy,
            failed,
        ),
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert any(
        "1350°F" in text
        for text in painter.text
    )

    assert not any(
        "2500°F" in text
        for text in painter.text
    )

    assert any(
        "---°F" in text
        for text in painter.text
    )

def test_invalid_hot_cht_does_not_trigger_high_cht_annunciator() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        cht_f=[
            350.0,
            350.0,
            700.0,
            350.0,
            350.0,
            350.0,
        ],
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    invalid = EngineChannelStatus(
        valid=False,
        fresh=False,
        message="IMPLAUSIBLE DATA",
    )

    sensor_status = EngineSensorStatus(
        cht=(
            healthy,
            healthy,
            invalid,
            healthy,
            healthy,
            healthy,
        ),
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert not any(
        text == "HIGH CHT"
        for text in painter.text
    )


def test_valid_hot_cht_still_triggers_high_cht_annunciator() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        cht_f=[
            350.0,
            350.0,
            460.0,
            350.0,
            350.0,
            350.0,
        ],
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    sensor_status = EngineSensorStatus(
        cht=(
            healthy,
            healthy,
            healthy,
            healthy,
            healthy,
            healthy,
        ),
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert any(
        text == "HIGH CHT"
        for text in painter.text
    )

def test_invalid_electrical_status_shows_alt_unavailable_without_alt_fail() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        rpm=2450.0,
        volts=0.0,
        amps=0.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[350.0] * 6,
        egt_f=[1350.0, 1360.0],
        ignition_a=True,
        ignition_b=True,
        alternator_online=False,
        fuel_remaining_gal=20.0,
        endurance_hr=3.0,
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    invalid = EngineChannelStatus(
        valid=False,
        fresh=False,
        message="IMPLAUSIBLE DATA",
    )

    sensor_status = EngineSensorStatus(
        rpm=healthy,
        volts=invalid,
        amps=invalid,
        oil_pressure=healthy,
        oil_temperature=healthy,
        fuel_pressure=healthy,
        fuel_flow=healthy,
        cht=(healthy,) * 6,
        egt=(healthy,) * 2,
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert "ALT ---" in painter.text

    assert not any(
        text == "ALT FAIL"
        for text in painter.text
    )


def test_valid_electrical_status_still_shows_alt_failure() -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.core.engine_sensor_status import (
        EngineChannelStatus,
        EngineSensorStatus,
    )
    from pyefis.user.blake_pfd.engine_data import EngineData

    page = EmsPage()
    painter = RecordingPainter()

    engine = EngineData(
        rpm=2450.0,
        volts=14.2,
        amps=5.0,
        oil_pressure_psi=45.0,
        oil_temp_f=190.0,
        cht_f=[350.0] * 6,
        egt_f=[1350.0, 1360.0],
        ignition_a=True,
        ignition_b=True,
        alternator_online=False,
        fuel_remaining_gal=20.0,
        endurance_hr=3.0,
    )

    engine_state = SimpleNamespace(
        data=engine,
        health=SimpleNamespace(),
        analysis=SimpleNamespace(),
        trend=SimpleNamespace(),
        cylinders=SimpleNamespace(),
        advice=None,
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    healthy = EngineChannelStatus(
        valid=True,
        fresh=True,
        message="DATA VALID",
    )

    sensor_status = EngineSensorStatus(
        rpm=healthy,
        volts=healthy,
        amps=healthy,
        oil_pressure=healthy,
        oil_temperature=healthy,
        fuel_pressure=healthy,
        fuel_flow=healthy,
        cht=(healthy,) * 6,
        egt=(healthy,) * 2,
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        sensor_status=sensor_status,
    )

    assert "ALT OFF" in painter.text

    assert any(
        text == "ALT FAIL"
        for text in painter.text
    )
