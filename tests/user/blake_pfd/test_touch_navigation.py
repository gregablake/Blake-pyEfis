import pytest

from pyefis.user.blake_pfd.core.touch_navigation import (
    TouchNavigation,
)


def test_creates_five_large_navigation_buttons() -> None:
    navigation = TouchNavigation()

    state = navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page="PFD",
    )

    assert len(state.buttons) == 5

    assert [
        button.label
        for button in state.buttons
    ] == [
        "PFD",
        "MAP",
        "ENGINE",
        "NEAREST",
        "SETTINGS",
    ]

    for button in state.buttons:
        assert button.bounds.height == 64.0
        assert button.bounds.width > 150.0


def test_pfd_is_selected() -> None:
    navigation = TouchNavigation()

    state = navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page="PFD",
    )

    assert state.buttons[0].selected is True

    assert all(
        button.selected is False
        for button in state.buttons[1:]
    )


def test_touch_returns_engine_page() -> None:
    navigation = TouchNavigation()

    state = navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page="PFD",
    )

    engine_button = state.buttons[2]

    selected_page = navigation.page_for_touch(
        point_x=(
            engine_button.bounds.x
            + engine_button.bounds.width / 2.0
        ),
        point_y=(
            engine_button.bounds.y
            + engine_button.bounds.height / 2.0
        ),
    )

    assert selected_page == "EMS"


def test_touch_returns_map_page() -> None:
    navigation = TouchNavigation()

    state = navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page="PFD",
    )

    map_button = state.buttons[1]

    selected_page = navigation.page_for_touch(
        point_x=(
            map_button.bounds.x
            + 10.0
        ),
        point_y=(
            map_button.bounds.y
            + 10.0
        ),
    )

    assert selected_page == "MAP"


def test_touch_outside_navigation_returns_none() -> None:
    navigation = TouchNavigation()

    navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page="PFD",
    )

    assert (
        navigation.page_for_touch(
            point_x=500.0,
            point_y=200.0,
        )
        is None
    )


def test_invalid_touch_returns_none() -> None:
    navigation = TouchNavigation()

    navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page="PFD",
    )

    assert (
        navigation.page_for_touch(
            point_x="bad",
            point_y=500.0,
        )
        is None
    )


def test_invalid_screen_does_not_create_buttons() -> None:
    navigation = TouchNavigation()

    state = navigation.layout(
        screen_width=0,
        screen_height=600,
        current_page="PFD",
    )

    assert state.buttons == ()


def test_constructor_rejects_bad_dimensions() -> None:
    with pytest.raises(ValueError):
        TouchNavigation(
            bar_height=0.0,
        )

    with pytest.raises(ValueError):
        TouchNavigation(
            margin=-1.0,
        )

    with pytest.raises(ValueError):
        TouchNavigation(
            spacing=-1.0,
        )