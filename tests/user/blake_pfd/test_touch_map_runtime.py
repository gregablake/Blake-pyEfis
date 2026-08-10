from pyefis.user.blake_pfd.core.touch_map_controls import (
    TouchMapControls,
)


def apply_map_action(
    range_nm: float,
    action: str | None,
) -> float:
    if action == "zoom_in":
        return max(
            2.0,
            range_nm / 2.0,
        )

    if action == "zoom_out":
        return min(
            200.0,
            range_nm * 2.0,
        )

    return range_nm


def test_zoom_in_halves_range() -> None:
    assert (
        apply_map_action(
            25.0,
            "zoom_in",
        )
        == 12.5
    )


def test_zoom_out_doubles_range() -> None:
    assert (
        apply_map_action(
            25.0,
            "zoom_out",
        )
        == 50.0
    )


def test_zoom_in_stops_at_two_nm() -> None:
    range_nm = 25.0

    for _ in range(10):
        range_nm = apply_map_action(
            range_nm,
            "zoom_in",
        )

    assert range_nm == 2.0


def test_zoom_out_stops_at_two_hundred_nm() -> None:
    range_nm = 25.0

    for _ in range(10):
        range_nm = apply_map_action(
            range_nm,
            "zoom_out",
        )

    assert range_nm == 200.0


def test_center_does_not_change_range() -> None:
    assert (
        apply_map_action(
            25.0,
            "center",
        )
        == 25.0
    )


def test_touch_action_drives_zoom_in() -> None:
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

    new_range = apply_map_action(
        25.0,
        action,
    )

    assert action == "zoom_in"
    assert new_range == 12.5


def test_touch_action_drives_zoom_out() -> None:
    controls = TouchMapControls()

    state = controls.layout(
        screen_width=1024,
        screen_height=600,
    )

    button = state.buttons[1]

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

    new_range = apply_map_action(
        25.0,
        action,
    )

    assert action == "zoom_out"
    assert new_range == 50.0