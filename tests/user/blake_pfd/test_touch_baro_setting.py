import pytest

from pyefis.user.blake_pfd.core.touch_baro_setting import (
    TouchBaroSetting,
)


def test_creates_large_decrement_and_increment_buttons():
    control = TouchBaroSetting()

    state = control.layout(
        screen_width=1024,
        screen_height=600,
    )

    assert state.valid is True

    assert state.decrement_bounds.width >= 150.0
    assert state.increment_bounds.width >= 150.0

    assert state.decrement_bounds.height >= 60.0
    assert state.increment_bounds.height >= 60.0

    assert state.value_bounds.width > 200.0


def test_decrement_touch_returns_decrement():
    control = TouchBaroSetting()

    state = control.layout(
        screen_width=1024,
        screen_height=600,
    )

    action = control.action_for_touch(
        point_x=(
            state.decrement_bounds.x
            + state.decrement_bounds.width / 2.0
        ),
        point_y=(
            state.decrement_bounds.y
            + state.decrement_bounds.height / 2.0
        ),
    )

    assert action == "decrement"


def test_increment_touch_returns_increment():
    control = TouchBaroSetting()

    state = control.layout(
        screen_width=1024,
        screen_height=600,
    )

    action = control.action_for_touch(
        point_x=(
            state.increment_bounds.x
            + state.increment_bounds.width / 2.0
        ),
        point_y=(
            state.increment_bounds.y
            + state.increment_bounds.height / 2.0
        ),
    )

    assert action == "increment"


def test_value_area_is_not_an_adjustment_button():
    control = TouchBaroSetting()

    state = control.layout(
        screen_width=1024,
        screen_height=600,
    )

    action = control.action_for_touch(
        point_x=(
            state.value_bounds.x
            + state.value_bounds.width / 2.0
        ),
        point_y=(
            state.value_bounds.y
            + state.value_bounds.height / 2.0
        ),
    )

    assert action is None


def test_touch_outside_returns_none():
    control = TouchBaroSetting()

    control.layout(
        screen_width=1024,
        screen_height=600,
    )

    assert (
        control.action_for_touch(
            point_x=10.0,
            point_y=10.0,
        )
        is None
    )


def test_invalid_screen_fails_closed():
    control = TouchBaroSetting()

    state = control.layout(
        screen_width=0,
        screen_height=600,
    )

    assert state.valid is False

    assert (
        control.action_for_touch(
            point_x=100.0,
            point_y=100.0,
        )
        is None
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"side_margin": -1.0},
        {"button_height": 0.0},
        {"spacing": -1.0},
        {"row_y": -1.0},
    ],
)
def test_constructor_rejects_bad_geometry(
    kwargs,
):
    with pytest.raises(ValueError):
        TouchBaroSetting(**kwargs)
