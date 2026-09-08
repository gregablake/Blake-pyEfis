from __future__ import annotations

import csv

import pytest

from PyQt6.QtCore import QPoint, Qt

from pyefis.user.blake_pfd.core.baro_setting_store import (
    BaroSettingStore,
)
from pyefis.user.blake_pfd.core.touch_baro_setting import (
    TouchBaroSetting,
)
from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


def write_replay_log(
    path,
    *,
    baro_setting_inhg: float,
    indicated_alt_ft: float,
) -> None:
    row = {
        "pressure_alt_ft": "1500.0",
        "indicated_alt_ft": str(
            indicated_alt_ft
        ),
        "baro_setting_inhg": str(
            baro_setting_inhg
        ),
    }

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file_handle:
        writer = csv.DictWriter(
            file_handle,
            fieldnames=list(
                row.keys()
            ),
        )
        writer.writeheader()
        writer.writerow(row)


def test_normal_startup_restores_persisted_baro(
    qtbot,
    tmp_path,
):
    state_path = (
        tmp_path
        / "baro.json"
    )

    BaroSettingStore(
        state_path
    ).save(
        30.17
    )

    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=state_path,
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    assert (
        widget.flight_computer
        .baro_setting_controller
        .setting_inhg
        == pytest.approx(30.17)
    )

    widget.close()


def test_missing_state_keeps_configured_default(
    qtbot,
    tmp_path,
):
    state_path = (
        tmp_path
        / "missing.json"
    )

    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=state_path,
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    assert (
        widget.flight_computer
        .baro_setting_controller
        .setting_inhg
        == pytest.approx(29.92)
    )

    widget.close()


def test_replay_ignores_persisted_baro_and_uses_log(
    qtbot,
    tmp_path,
):
    state_path = (
        tmp_path
        / "baro.json"
    )

    replay_path = (
        tmp_path
        / "replay.csv"
    )

    BaroSettingStore(
        state_path
    ).save(
        30.45
    )

    write_replay_log(
        replay_path,
        baro_setting_inhg=29.81,
        indicated_alt_ft=1400.0,
    )

    widget = BlakePfdDemo(
        use_hardware=False,
        replay_log=str(
            replay_path
        ),
        baro_state_path=state_path,
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    result = (
        widget.sensor_manager
        .read_flight()
    )

    assert (
        result.baro_setting_inhg
        == pytest.approx(29.81)
    )

    assert (
        widget.flight_computer
        .baro_setting_controller
        .setting_inhg
        == pytest.approx(29.81)
    )

    # Replay must not overwrite the pilot's
    # persisted live-operation setting.
    assert (
        BaroSettingStore(
            state_path
        ).load(
            default_inhg=29.92
        )
        == pytest.approx(30.45)
    )

    widget.close()


@pytest.mark.parametrize(
    (
        "action",
        "expected",
    ),
    [
        (
            "increment",
            29.93,
        ),
        (
            "decrement",
            29.91,
        ),
    ],
)
def test_baro_touch_persists_new_setting(
    qtbot,
    tmp_path,
    action,
    expected,
):
    state_path = (
        tmp_path
        / "baro.json"
    )

    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=state_path,
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

    geometry = TouchBaroSetting()

    state = geometry.layout(
        screen_width=widget.width(),
        screen_height=widget.height(),
    )

    assert state.valid is True

    if action == "increment":
        bounds = (
            state.increment_bounds
        )
    else:
        bounds = (
            state.decrement_bounds
        )

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

    assert (
        BaroSettingStore(
            state_path
        ).load(
            default_inhg=29.92
        )
        == pytest.approx(expected)
    )

    widget.close()


def test_baro_adjustment_survives_persistence_failure(
    qtbot,
    tmp_path,
):
    state_path = (
        tmp_path
        / "baro.json"
    )

    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=state_path,
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

    def fail_save(
        value_inhg,
    ):
        raise OSError(
            "simulated storage failure"
        )

    widget.baro_setting_store.save = (
        fail_save
    )

    geometry = TouchBaroSetting()

    state = geometry.layout(
        screen_width=widget.width(),
        screen_height=widget.height(),
    )

    bounds = state.increment_bounds

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

    # Persistence is secondary. The pilot's live
    # BARO adjustment must still take effect.
    assert (
        widget.flight_computer
        .baro_setting_controller
        .setting_inhg
        == pytest.approx(29.93)
    )

    widget.close()
