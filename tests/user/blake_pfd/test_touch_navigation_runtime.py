from pyefis.user.blake_pfd.core.page_manager import (
    PageManager,
)
from pyefis.user.blake_pfd.core.touch_navigation import (
    TouchNavigation,
)


def build_page_manager() -> PageManager:
    manager = PageManager()

    manager.register(
        "PFD",
        "P",
    )
    manager.register(
        "MAP",
        "M",
    )
    manager.register(
        "EMS",
        "E",
    )
    manager.register(
        "NEAREST",
        "N",
    )
    manager.register(
        "SETTINGS",
        "S",
    )

    return manager


def test_touch_navigation_switches_to_map() -> None:
    manager = build_page_manager()

    navigation = TouchNavigation()

    state = navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page=manager.current(),
    )

    map_button = state.buttons[1]

    selected_page = (
        navigation.page_for_touch(
            point_x=(
                map_button.bounds.x
                + map_button.bounds.width / 2.0
            ),
            point_y=(
                map_button.bounds.y
                + map_button.bounds.height / 2.0
            ),
        )
    )

    manager.set_page(
        selected_page
    )

    assert manager.current() == "MAP"


def test_touch_navigation_switches_to_engine() -> None:
    manager = build_page_manager()

    navigation = TouchNavigation()

    state = navigation.layout(
        screen_width=1024,
        screen_height=600,
        current_page="PFD",
    )

    engine_button = state.buttons[2]

    selected_page = (
        navigation.page_for_touch(
            point_x=(
                engine_button.bounds.x
                + 10.0
            ),
            point_y=(
                engine_button.bounds.y
                + 10.0
            ),
        )
    )

    manager.set_page(
        selected_page
    )

    assert manager.current() == "EMS"


def test_settings_page_can_be_selected() -> None:
    manager = build_page_manager()

    manager.set_page(
        "SETTINGS"
    )

    assert manager.current() == "SETTINGS"