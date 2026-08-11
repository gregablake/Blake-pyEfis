from pyefis.user.blake_pfd.core.map_orientation import (
    MapOrientation,
)


def test_track_up_places_track_ahead() -> None:
    orientation = MapOrientation(
        mode="TRACK_UP",
    )

    orientation.update_reference(
        track_deg=90.0,
    )

    relative = (
        orientation.relative_bearing_deg(
            bearing_deg=90.0,
        )
    )

    assert relative == 0.0


def test_track_up_places_right_side_at_90_deg() -> None:
    orientation = MapOrientation(
        mode="TRACK_UP",
    )

    orientation.update_reference(
        track_deg=90.0,
    )

    relative = (
        orientation.relative_bearing_deg(
            bearing_deg=180.0,
        )
    )

    assert relative == 90.0


def test_north_up_keeps_true_bearing() -> None:
    orientation = MapOrientation(
        mode="NORTH_UP",
    )

    orientation.update_reference(
        track_deg=240.0,
    )

    relative = (
        orientation.relative_bearing_deg(
            bearing_deg=135.0,
        )
    )

    assert relative == 135.0


def test_toggle_changes_display_reference() -> None:
    orientation = MapOrientation()

    orientation.update_reference(
        track_deg=90.0,
    )

    assert (
        orientation.relative_bearing_deg(
            bearing_deg=90.0,
        )
        == 90.0
    )

    orientation.toggle()

    orientation.update_reference(
        track_deg=90.0,
    )

    assert (
        orientation.relative_bearing_deg(
            bearing_deg=90.0,
        )
        == 0.0
    )