"""V6 scenic PFD stays visible; real checklist behavior remains unchanged."""
import pytest
from types import SimpleNamespace
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


@pytest.mark.parametrize(
    "v6, mountain, scenic, hardware, allowed",
    [
        ("1", "1", "0", False, False),
        ("1", "0", "1", False, False),
        ("1", "0", "0", False, True),
        ("0", "1", "0", False, True),
        ("1", "1", "0", True, True),
        ("0", "0", "0", True, True),
    ],
)
def test_automatic_checklist_takes_over_only_outside_scenic_demo(
    monkeypatch, v6, mountain, scenic, hardware, allowed,
):
    monkeypatch.setenv("BLAKE_PFD_V6_VISUALS", v6)
    monkeypatch.setenv("BLAKE_PFD_MOUNTAIN_DEMO", mountain)
    monkeypatch.setenv("BLAKE_PFD_SCENIC_DEMO", scenic)
    widget_stub = SimpleNamespace(use_hardware=hardware)
    assert BlakePfdDemo._automatic_checklist_popup_allowed(widget_stub) is allowed
