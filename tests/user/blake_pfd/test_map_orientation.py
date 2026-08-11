import pytest

from pyefis.user.blake_pfd.core.map_orientation import (
    MapOrientation,
)


def test_default_mode_is_north_up() -> None:
    orientation = MapOrientation()

    assert orientation.state.mode == "NORTH_UP"
    assert orientation.state.reference_deg == 0.0


def test_north_up_ignores_track() -> None:
    orientation = MapOrientation()

    state = orientation.update_reference(
        track_deg=123.0,
    )

    assert state.reference_deg == 0.0


def test_track_up_uses_aircraft_track() -> None:
    orientation = MapOrientation(
        mode="TRACK_UP",
    )

    state = orientation.update_reference(
        track_deg=123.0,
    )

    assert state.reference_deg == 123.0


def test_track_is_normalized() -> None:
    orientation = MapOrientation(
        mode="TRACK_UP",
    )

    state = orientation.update_reference(
        track_deg=370.0,
    )

    assert state.reference_deg == 10.0


def test_relative_bearing_north_up() -> None:
    orientation = MapOrientation()

    bearing = orientation.relative_bearing_deg(
        bearing_deg=90.0,
    )

    assert bearing == 90.0


def test_relative_bearing_track_up() -> None:
    orientation = MapOrientation(
        mode="TRACK_UP",
    )

    orientation.update_reference(
        track_deg=90.0,
    )

    bearing = orientation.relative_bearing_deg(
        bearing_deg=135.0,
    )

    assert bearing == 45.0


def test_relative_bearing_wraps() -> None:
    orientation = MapOrientation(
        mode="TRACK_UP",
    )

    orientation.update_reference(
        track_deg=350.0,
    )

    bearing = orientation.relative_bearing_deg(
        bearing_deg=10.0,
    )

    assert bearing == 20.0


def test_toggle_switches_modes() -> None:
    orientation = MapOrientation()

    state = orientation.toggle()

    assert state.mode == "TRACK_UP"

    state = orientation.toggle()

    assert state.mode == "NORTH_UP"


def test_invalid_bearing_returns_none() -> None:
    orientation = MapOrientation()

    assert (
        orientation.relative_bearing_deg(
            bearing_deg="bad",
        )
        is None
    )


def test_invalid_mode_raises() -> None:
    with pytest.raises(ValueError):
        MapOrientation(
            mode="SIDEWAYS",
        )