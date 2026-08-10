from pyefis.user.blake_pfd.core.map_viewport import (
    MapViewport,
)


def test_drag_sequence_moves_viewport() -> None:
    viewport = MapViewport()

    start_x = 400.0
    start_y = 300.0

    next_x = 450.0
    next_y = 275.0

    state = viewport.pan_by(
        delta_x_px=(
            next_x - start_x
        ),
        delta_y_px=(
            next_y - start_y
        ),
    )

    assert state.offset_x_px == 50.0
    assert state.offset_y_px == -25.0
    assert state.centered is False


def test_multiple_drag_updates_accumulate() -> None:
    viewport = MapViewport()

    viewport.pan_by(
        delta_x_px=30.0,
        delta_y_px=20.0,
    )

    state = viewport.pan_by(
        delta_x_px=-10.0,
        delta_y_px=15.0,
    )

    assert state.offset_x_px == 20.0
    assert state.offset_y_px == 35.0


def test_center_button_restores_aircraft_center() -> None:
    viewport = MapViewport()

    viewport.pan_by(
        delta_x_px=125.0,
        delta_y_px=-80.0,
    )

    state = viewport.center()

    assert state.centered is True
    assert state.offset_x_px == 0.0
    assert state.offset_y_px == 0.0


def test_pan_cannot_exceed_limit() -> None:
    viewport = MapViewport(
        maximum_offset_px=500.0,
    )

    state = viewport.pan_by(
        delta_x_px=5000.0,
        delta_y_px=-5000.0,
    )

    assert state.offset_x_px == 500.0
    assert state.offset_y_px == -500.0