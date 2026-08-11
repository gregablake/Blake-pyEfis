import pytest

from pyefis.user.blake_pfd.core.touch_map_controls import (
    TouchMapControls,
)


def test_map_controls_create_three_buttons() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    assert len(state.buttons) == 4

    assert [
        button.label
        for button in state.buttons
    ] == [
        "+",
        "-",
        "CTR",
        "N/TRK",
    ]


def test_buttons_are_touch_friendly() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    for button in state.buttons:
        assert button.bounds.width >= 72.0
        assert button.bounds.height >= 64.0


def test_zoom_in_touch() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    button = state.buttons[0]

    action = controls.action_for_touch(
        point_x=(
            button.bounds.x
            + button.bounds.width / 2.0
        ),
        point_y=(
            button.bounds.y
            + button.bounds.height / 2.0
        ),
    )

    assert action == "zoom_in"


def test_zoom_out_touch() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    button = state.buttons[1]

    action = controls.action_for_touch(
        point_x=button.bounds.x + 10.0,
        point_y=button.bounds.y + 10.0,
    )

    assert action == "zoom_out"


def test_center_touch() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    button = state.buttons[2]

    action = controls.action_for_touch(
        point_x=button.bounds.x + 10.0,
        point_y=button.bounds.y + 10.0,
    )

    assert action == "center"


def test_touch_outside_returns_none() -> None:
    controls = TouchMapControls()

    controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    assert (
        controls.action_for_touch(
            point_x=200.0,
            point_y=200.0,
        )
        is None
    )


def test_invalid_screen_returns_no_buttons() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=0,
        screen_height=600,
    )

    assert state.buttons == ()


def test_constructor_rejects_bad_values() -> None:
    with pytest.raises(ValueError):
        TouchMapControls(
            button_width=0.0,
        )

    with pytest.raises(ValueError):
        TouchMapControls(
            button_height=-1.0,
        )

    with pytest.raises(ValueError):
        TouchMapControls(
            spacing=-1.0,
        )
        
def test_orientation_touch() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    button = state.buttons[3]

    action = controls.action_for_touch(
        point_x=(
            button.bounds.x
            + button.bounds.width / 2.0
        ),
        point_y=(
            button.bounds.y
            + button.bounds.height / 2.0
        ),
    )

    assert action == "orientation"