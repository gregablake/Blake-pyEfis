from types import SimpleNamespace

import pyefis.user.blake_pfd.master_warning as warning_module

from pyefis.user.blake_pfd.master_warning import (
    draw_master_warning_strip,
    get_checklist_warnings,
    get_engine_warnings,
)

def engine(**overrides):
    values = {
        "rpm": 2200.0,
        "oil_pressure_psi": 45.0,
        "oil_temp_f": 210.0,
        "cht_f": [350.0] * 6,
        "egt_f": [1350.0] * 6,
        "volts": 14.2,
        "alternator_online": True,
        "ignition_a": True,
        "ignition_b": True,
        "starter_engaged": False,
        "fuel_remaining_gal": 20.0,
        "endurance_hr": 2.5,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_normal_engine_has_no_engine_warnings() -> None:
    warnings = get_engine_warnings(engine())

    assert warnings == []


def test_low_oil_pressure_creates_red_warning() -> None:
    warnings = get_engine_warnings(
        engine(oil_pressure_psi=12.0)
    )

    texts = [warning.text for warning in warnings]

    assert "LOW OIL PRESS" in texts
    assert "OIL PRESS" in texts


def test_high_cht_creates_warning() -> None:
    warnings = get_engine_warnings(
        engine(cht_f=[350.0, 355.0, 455.0, 360.0, 365.0, 350.0])
    )

    texts = [warning.text for warning in warnings]

    assert "HIGH CHT" in texts


def test_incomplete_takeoff_checklist_creates_warning() -> None:
    checklist = SimpleNamespace(
        active_phase_complete=lambda: False
    )

    warnings = get_checklist_warnings(
        checklist=checklist,
        aircraft_moving=True,
        flight_phase="TAKEOFF",
    )

    assert len(warnings) == 1
    assert warnings[0].text == "CHECKLIST"


def test_complete_checklist_has_no_warning() -> None:
    checklist = SimpleNamespace(
        active_phase_complete=lambda: True
    )

    warnings = get_checklist_warnings(
        checklist=checklist,
        aircraft_moving=True,
        flight_phase="TAKEOFF",
    )

    assert warnings == []
    
class FakePainter:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def setFont(self, *args, **kwargs) -> None:
        pass

    def fillRect(self, *args, **kwargs) -> None:
        pass

    def setPen(self, *args, **kwargs) -> None:
        pass

    def drawText(self, *args, **kwargs) -> None:
        if args and isinstance(args[-1], str):
            self.texts.append(args[-1])


def test_ai_warning_includes_urgency(monkeypatch) -> None:
    monkeypatch.setattr(
        warning_module,
        "load_config",
        lambda: SimpleNamespace(
            fuel=SimpleNamespace(
                red_gal=3.0,
                yellow_gal=6.0,
                red_endurance_hr=0.3,
                yellow_endurance_hr=0.6,
            ),
            ems_test=SimpleNamespace(mode="normal"),
        ),
    )

    recommendation = SimpleNamespace(
        severity="CAUTION",
        title="Predicted Engine Limit",
        urgency_s=28.0,
    )

    painter = FakePainter()

    draw_master_warning_strip(
        painter=painter,
        engine=engine(),
        width=1000,
        checklist=None,
        aircraft_moving=False,
        aircraft_recommendation=recommendation,
    )

    assert any(
        "AI PREDICTED ENGINE LIMIT 28s" in text
        for text in painter.texts
    )