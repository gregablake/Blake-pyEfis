import pytest

from pyefis.user.blake_pfd.core.pfd_layout import (
    PfdLayout,
)


def test_1024x600_layout_matches_design() -> None:
    layout = PfdLayout.build(
        1024,
        600,
    )

    assert layout.top_bar.height == 36

    assert layout.left_panel.x == 0
    assert layout.left_panel.width == 180

    assert layout.flight_view.x == 180
    assert layout.flight_view.width == 644

    assert layout.right_panel.x == 824
    assert layout.right_panel.width == 200

    assert layout.bottom_bar.y == 570
    assert layout.bottom_bar.height == 30


def test_main_regions_tile_screen_width() -> None:
    layout = PfdLayout.build(
        1024,
        600,
    )

    assert (
        layout.left_panel.width
        + layout.flight_view.width
        + layout.right_panel.width
        == layout.screen.width
    )

    assert (
        layout.left_panel.right
        == layout.flight_view.x
    )

    assert (
        layout.flight_view.right
        == layout.right_panel.x
    )

    assert (
        layout.right_panel.right
        == layout.screen.right
    )


def test_main_regions_share_vertical_bounds() -> None:
    layout = PfdLayout.build(
        1024,
        600,
    )

    assert (
        layout.left_panel.y
        == layout.flight_view.y
        == layout.right_panel.y
        == layout.top_bar.bottom
    )

    assert (
        layout.left_panel.bottom
        == layout.flight_view.bottom
        == layout.right_panel.bottom
        == layout.bottom_bar.y
    )


def test_layout_scales_to_larger_render() -> None:
    layout = PfdLayout.build(
        1280,
        720,
    )

    assert layout.screen.width == 1280
    assert layout.screen.height == 720

    assert (
        layout.left_panel.width
        + layout.flight_view.width
        + layout.right_panel.width
        == 1280
    )


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (0, 600),
        (1024, 0),
        (-1, 600),
        (1024, -1),
    ],
)
def test_invalid_screen_size_rejected(
    width,
    height,
) -> None:
    with pytest.raises(ValueError):
        PfdLayout.build(
            width,
            height,
        )
