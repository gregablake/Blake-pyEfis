from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
    TouchGuidanceMenu,
)


def test_touch_runtime_toggles_guidance() -> None:
    menu = TouchGuidanceMenu()

    state = menu.open(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(
            hits_enabled=True,
            flight_director_enabled=True,
        ),
    )

    hits_button = state.buttons[0]

    state = menu.handle_touch(
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
        state.settings.hits_enabled
        is False
    )

    director_button = state.buttons[1]

    state = menu.handle_touch(
        point_x=(
            director_button.bounds.x
            + director_button.bounds.width / 2.0
        ),
        point_y=(
            director_button.bounds.y
            + director_button.bounds.height / 2.0
        ),
    )

    assert (
        state.settings
        .flight_director_enabled
        is False
    )


def test_touch_runtime_preserves_other_settings() -> None:
    menu = TouchGuidanceMenu()

    state = menu.open(
        screen_width=1024,
        screen_height=600,
        settings=GuidanceTouchSettings(
            hits_enabled=True,
            flight_director_enabled=True,
            flight_path_marker_enabled=True,
            synthetic_vision_enabled=True,
        ),
    )

    button = state.buttons[0]

    state = menu.handle_touch(
        point_x=button.bounds.x + 5.0,
        point_y=button.bounds.y + 5.0,
    )

    assert (
        state.settings.hits_enabled
        is False
    )
    assert (
        state.settings
        .flight_director_enabled
        is True
    )
    assert (
        state.settings
        .flight_path_marker_enabled
        is True
    )
    assert (
        state.settings
        .synthetic_vision_enabled
        is True
    )