from pyefis.user.blake_pfd.core.checklist_manager import ChecklistManager


def test_normal_phase_does_not_popup() -> None:
    manager = ChecklistManager()

    state = manager.update("PARKED")

    assert state.active == "Preflight"
    assert state.should_popup is False
    assert state.popup_suppressed is False


def test_critical_phase_popups_once() -> None:
    manager = ChecklistManager()

    first = manager.update("RUNUP")
    second = manager.update("RUNUP")

    assert first.should_popup is True
    assert second.should_popup is False


def test_suppressed_phase_does_not_popup() -> None:
    manager = ChecklistManager()

    manager.suppress_for_phase("TAKEOFF")
    state = manager.update("TAKEOFF")

    assert state.active == "Before Takeoff"
    assert state.should_popup is False
    assert state.popup_suppressed is True


def test_clear_suppression_restores_popup_eligibility() -> None:
    manager = ChecklistManager()

    manager.suppress_for_phase("DESCENT")
    suppressed = manager.update("DESCENT")

    manager.clear_suppression()
    restored = manager.update("DESCENT")

    assert suppressed.popup_suppressed is True
    assert restored.popup_suppressed is False
    assert restored.should_popup is True


def test_new_phase_can_popup_after_previous_phase() -> None:
    manager = ChecklistManager()

    runup = manager.update("RUNUP")
    takeoff = manager.update("TAKEOFF")

    assert runup.should_popup is True
    assert takeoff.should_popup is True