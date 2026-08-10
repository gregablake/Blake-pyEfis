import pytest

from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
)
from pyefis.user.blake_pfd.core.touch_settings import (
    TouchSettings,
)


def test_creates_large_settings_buttons() -> None:
    settings = TouchSettings()

    state = settings.layout(
        screen_width=1024,
        screen_height=600,
        values=GuidanceTouchSettings(),
    )

    assert len(state.buttons) == 4

    assert [
        button.label
        for button in state.buttons
    ] == [
        "HITS",
        "FLIGHT DIRECTOR",
        "FLIGHT PATH MARKER",
        "SYNTHETIC VISION",
    ]

    for button in state.buttons:
        assert button.bounds.height == 72.0
        assert button.bounds.width > 800.0


def test_button_states_match_values() -> None:
    settings = TouchSettings()

    state = settings.layout(
        screen_width=1024,
        screen_height=600,
        values=GuidanceTouchSettings(
            hits_enabled=False,
            flight_director_enabled=True,
            flight_path_marker_enabled=False,
            synthetic_vision_enabled=True,
        ),
    )

    assert state.buttons[0].enabled is False
    assert state.buttons[1].enabled is True
    assert state.buttons[2].enabled is False
    assert state.buttons[3].enabled is True


def test_touch_returns_hits_key() -> None:
    settings = TouchSettings()

    state = settings.layout(
        screen_width=1024,
        screen_height=600,
        values=GuidanceTouchSettings(),
    )

    button = state.buttons[0]

    key = settings.key_for_touch(
        point_x=(
            button.bounds.x
            + button.bounds.width / 2.0
        ),
        point_y=(
            button.bounds.y
            + button.bounds.height / 2.0
        ),
    )

    assert key == "hits_enabled"


def test_touch_returns_synthetic_vision_key() -> None:
    settings = TouchSettings()

    state = settings.layout(
        screen_width=1024,
        screen_height=600,
        values=GuidanceTouchSettings(),
    )

    button = state.buttons[3]

    key = settings.key_for_touch(
        point_x=button.bounds.x + 10.0,
        point_y=button.bounds.y + 10.0,
    )

    assert key == "synthetic_vision_enabled"


def test_touch_outside_returns_none() -> None:
    settings = TouchSettings()

    settings.layout(
        screen_width=1024,
        screen_height=600,
        values=GuidanceTouchSettings(),
    )

    assert (
        settings.key_for_touch(
            point_x=10.0,
            point_y=10.0,
        )
        is None
    )


def test_invalid_screen_has_no_buttons() -> None:
    settings = TouchSettings()

    state = settings.layout(
        screen_width=0,
        screen_height=600,
        values=GuidanceTouchSettings(),
    )

    assert state.buttons == ()


def test_constructor_rejects_bad_dimensions() -> None:
    with pytest.raises(ValueError):
        TouchSettings(
            button_height=0.0,
        )

    with pytest.raises(ValueError):
        TouchSettings(
            side_margin=-1.0,
        )

    with pytest.raises(ValueError):
        TouchSettings(
            spacing=-1.0,
        )