import pytest

from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
    TouchGuidanceMenu,
)


def test_menu_opens_with_large_touch_buttons() -> None:
    menu = TouchGuidanceMenu(
        button_height=64.0,
    )

    state = menu.open(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(),
    )

    assert state.visible is True
    assert len(state.buttons) == 4

    for button in state.buttons:
        assert button.bounds.height == 64.0
        assert button.bounds.width > 300.0


def test_touch_toggles_hits() -> None:
    menu = TouchGuidanceMenu()

    state = menu.open(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(
            hits_enabled=True,
        ),
    )

    hits_button = state.buttons[0]

    updated = menu.handle_touch(
        point_x=(
            hits_button.bounds.x
            + hits_button.bounds.width / 2.0
        ),
        point_y=(
            hits_button.bounds.y
            + hits_button.bounds.height / 2.0
        ),
    )

    assert (
        updated.settings.hits_enabled
        is False
    )
    assert updated.buttons[0].enabled is False


def test_touch_toggles_flight_director() -> None:
    menu = TouchGuidanceMenu()

    state = menu.open(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(
            flight_director_enabled=False,
        ),
    )

    button = state.buttons[1]

    updated = menu.handle_touch(
        point_x=button.bounds.x + 10.0,
        point_y=button.bounds.y + 10.0,
    )

    assert (
        updated.settings
        .flight_director_enabled
        is True
    )


def test_touch_outside_buttons_changes_nothing() -> None:
    menu = TouchGuidanceMenu()

    original = menu.open(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(),
    )

    updated = menu.handle_touch(
        point_x=10.0,
        point_y=10.0,
    )

    assert updated == original


def test_hidden_menu_ignores_touch() -> None:
    menu = TouchGuidanceMenu()

    state = menu.handle_touch(
        point_x=500.0,
        point_y=300.0,
    )

    assert state.visible is False
    assert state.settings.hits_enabled is True


def test_close_preserves_settings() -> None:
    menu = TouchGuidanceMenu()

    state = menu.open(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(
            hits_enabled=False,
        ),
    )

    assert state.visible is True

    closed = menu.close()

    assert closed.visible is False
    assert (
        closed.settings.hits_enabled
        is False
    )


def test_toggle_visibility_opens_and_closes() -> None:
    menu = TouchGuidanceMenu()

    opened = menu.toggle_visibility(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(),
    )

    assert opened.visible is True

    closed = menu.toggle_visibility(
        screen_width=1024,
        screen_height=600,
        settings=opened.settings,
    )

    assert closed.visible is False


def test_invalid_screen_size_does_not_open() -> None:
    menu = TouchGuidanceMenu()

    state = menu.open(
        screen_width=0,
        screen_height=600,
        settings=GuidanceTouchSettings(),
    )

    assert state.visible is False
    assert state.buttons == ()


def test_constructor_rejects_bad_dimensions() -> None:
    with pytest.raises(ValueError):
        TouchGuidanceMenu(
            panel_width=0.0,
        )

    with pytest.raises(ValueError):
        TouchGuidanceMenu(
            button_height=-1.0,
        )

    with pytest.raises(ValueError):
        TouchGuidanceMenu(
            button_spacing=-1.0,
        )