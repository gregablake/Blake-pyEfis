import pytest

from PyQt6.QtCore import QPoint, Qt

from pyefis.user.blake_pfd.core.touch_baro_setting import (
    TouchBaroSetting,
)
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def make_widget(
    qtbot,
):
    widget = BlakePfdDemo(
        use_hardware=False,
    )
    widget.timer.stop()

    widget.resize(
        1024,
        600,
    )

    qtbot.addWidget(widget)

    widget.page_manager.set_page(
        "SETTINGS"
    )

    assert (
        widget.flight_computer
        .baro_setting_controller
        .set_setting(29.92)
        is True
    )

    return widget


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("increment", 29.93),
        ("decrement", 29.91),
    ],
)
def test_settings_page_baro_touch_changes_live_controller(
    qtbot,
    action,
    expected,
):
    widget = make_widget(
        qtbot
    )

    geometry = TouchBaroSetting()

    state = geometry.layout(
        screen_width=widget.width(),
        screen_height=widget.height(),
    )

    assert state.valid is True

    if action == "increment":
        bounds = state.increment_bounds
    else:
        bounds = state.decrement_bounds

    point = QPoint(
        int(
            bounds.x
            + bounds.width / 2.0
        ),
        int(
            bounds.y
            + bounds.height / 2.0
        ),
    )

    qtbot.mouseClick(
        widget,
        Qt.MouseButton.LeftButton,
        pos=point,
    )

    assert (
        widget.flight_computer
        .baro_setting_controller
        .setting_inhg
        == pytest.approx(expected)
    )

    widget.close()
