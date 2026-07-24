from types import SimpleNamespace

import pyefis.user.blake_pfd.core.warning_manager as warning_module
from pyefis.user.blake_pfd.core.warning_manager import WarningManager


def test_warning_manager_passes_aircraft_moving_true(monkeypatch) -> None:
    captured = {}

    def fake_draw_master_warning_strip(
        painter,
        engine,
        width,
        checklist=None,
        aircraft_moving=False,
        aircraft_recommendation=None,
    ) -> None:
        captured["painter"] = painter
        captured["engine"] = engine
        captured["width"] = width
        captured["checklist"] = checklist
        captured["aircraft_moving"] = aircraft_moving
        captured["aircraft_recommendation"] = aircraft_recommendation

    monkeypatch.setattr(
        warning_module,
        "draw_master_warning_strip",
        fake_draw_master_warning_strip,
    )

    warning = SimpleNamespace(
        severity="WARNING",
        title="Engine Warning",
    )

    app = SimpleNamespace(
        pfd=SimpleNamespace(ground_speed_kt=40.0),
        engine_data=object(),
        engine_checklist_page=object(),
        aircraft_recommendation=warning,
    )

    manager = WarningManager(app)
    painter = object()

    manager.draw(painter, 1000)

    assert captured["painter"] is painter
    assert captured["engine"] is app.engine_data
    assert captured["width"] == 1000
    assert captured["checklist"] is app.engine_checklist_page
    assert captured["aircraft_moving"] is True
    assert captured["aircraft_recommendation"] is warning


def test_warning_manager_passes_aircraft_moving_false_without_pfd(
    monkeypatch,
) -> None:
    captured = {}

    def fake_draw_master_warning_strip(
        painter,
        engine,
        width,
        checklist=None,
        aircraft_moving=False,
        aircraft_recommendation=None,
    ) -> None:
        captured["aircraft_moving"] = aircraft_moving

    monkeypatch.setattr(
        warning_module,
        "draw_master_warning_strip",
        fake_draw_master_warning_strip,
    )

    app = SimpleNamespace(
        pfd=None,
        engine_data=object(),
        engine_checklist_page=object(),
        aircraft_recommendation=object(),
    )

    manager = WarningManager(app)
    manager.draw(object(), 1000)

    assert captured["aircraft_moving"] is False
    
def test_warning_manager_exposes_stabilizer_status() -> None:
    app = SimpleNamespace(
        pfd=None,
        engine_data=object(),
        engine_checklist_page=object(),
        aircraft_recommendation=SimpleNamespace(
            severity="NORMAL",
            title="Normal",
        ),
    )

    manager = WarningManager(app)

    status = manager.recommendation_status()

    assert status.state == "IDLE"
    assert status.active_title is None
    assert status.pending_title is None