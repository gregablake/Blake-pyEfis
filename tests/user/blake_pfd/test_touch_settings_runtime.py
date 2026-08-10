from dataclasses import replace

from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
)
from pyefis.user.blake_pfd.core.touch_settings import (
    TouchSettings,
)


def test_settings_touch_toggles_hits() -> None:
    values = GuidanceTouchSettings(
        hits_enabled=True,
    )

    settings = TouchSettings()

    state = settings.layout(
        screen_width=1024,
        screen_height=600,
        values=values,
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

    updated = replace(
        values,
        **{
            key: not getattr(
                values,
                key,
            )
        },
    )

    assert updated.hits_enabled is False


def test_settings_touch_preserves_other_values() -> None:
    values = GuidanceTouchSettings(
        hits_enabled=True,
        flight_director_enabled=True,
        flight_path_marker_enabled=True,
        synthetic_vision_enabled=True,
    )

    updated = replace(
        values,
        hits_enabled=False,
    )

    assert updated.hits_enabled is False

    assert (
        updated.flight_director_enabled
        is True
    )

    assert (
        updated.flight_path_marker_enabled
        is True
    )

    assert (
        updated.synthetic_vision_enabled
        is True
    )