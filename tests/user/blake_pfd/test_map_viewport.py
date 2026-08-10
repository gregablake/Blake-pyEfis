import pytest

from pyefis.user.blake_pfd.core.map_viewport import (
    MapViewport,
)


def test_viewport_starts_centered() -> None:
    viewport = MapViewport()

    assert viewport.state.centered is True
    assert viewport.state.offset_x_px == 0.0
    assert viewport.state.offset_y_px == 0.0


def test_pan_changes_offset() -> None:
    viewport = MapViewport()

    state = viewport.pan_by(
        delta_x_px=50.0,
        delta_y_px=-25.0,
    )

    assert state.offset_x_px == 50.0
    assert state.offset_y_px == -25.0
    assert state.centered is False


def test_multiple_pan_operations_accumulate() -> None:
    viewport = MapViewport()

    viewport.pan_by(
        delta_x_px=20.0,
        delta_y_px=10.0,
    )

    state = viewport.pan_by(
        delta_x_px=30.0,
        delta_y_px=-5.0,
    )

    assert state.offset_x_px == 50.0
    assert state.offset_y_px == 5.0


def test_center_resets_offsets() -> None:
    viewport = MapViewport()

    viewport.pan_by(
        delta_x_px=100.0,
        delta_y_px=75.0,
    )

    state = viewport.center()

    assert state.centered is True
    assert state.offset_x_px == 0.0
    assert state.offset_y_px == 0.0


def test_offsets_are_limited() -> None:
    viewport = MapViewport(
        maximum_offset_px=100.0,
    )

    state = viewport.pan_by(
        delta_x_px=500.0,
        delta_y_px=-500.0,
    )

    assert state.offset_x_px == 100.0
    assert state.offset_y_px == -100.0


def test_invalid_pan_is_ignored() -> None:
    viewport = MapViewport()

    original = viewport.state

    state = viewport.pan_by(
        delta_x_px="bad",
        delta_y_px=10.0,
    )

    assert state == original


def test_returning_to_zero_is_centered() -> None:
    viewport = MapViewport()

    viewport.pan_by(
        delta_x_px=50.0,
        delta_y_px=25.0,
    )

    state = viewport.pan_by(
        delta_x_px=-50.0,
        delta_y_px=-25.0,
    )

    assert state.centered is True


def test_constructor_rejects_bad_limit() -> None:
    with pytest.raises(ValueError):
        MapViewport(
            maximum_offset_px=0.0,
        )

    with pytest.raises(ValueError):
        MapViewport(
            maximum_offset_px=-1.0,
        )