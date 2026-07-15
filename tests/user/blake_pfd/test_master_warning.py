from types import SimpleNamespace

from pyefis.user.blake_pfd.master_warning import (
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