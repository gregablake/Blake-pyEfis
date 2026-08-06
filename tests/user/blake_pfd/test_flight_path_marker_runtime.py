from pyefis.user.blake_pfd.core.flight_path_marker import (
    FlightPathMarker,
)


def test_runtime_marker_uses_heading_and_track() -> None:
    marker = FlightPathMarker().calculate(
        track_deg=100.0,
        heading_deg=90.0,
        ground_speed_kt=100.0,
        vertical_speed_fpm=0.0,
    )

    assert marker.valid is True
    assert marker.x_offset_deg == 10.0


def test_runtime_marker_wraps_heading_difference() -> None:
    marker = FlightPathMarker().calculate(
        track_deg=5.0,
        heading_deg=355.0,
        ground_speed_kt=100.0,
        vertical_speed_fpm=0.0,
    )

    assert marker.valid is True
    assert marker.x_offset_deg == 10.0


def test_runtime_marker_moves_up_in_climb() -> None:
    marker = FlightPathMarker().calculate(
        track_deg=90.0,
        heading_deg=90.0,
        ground_speed_kt=100.0,
        vertical_speed_fpm=1000.0,
    )

    assert marker.valid is True
    assert marker.y_offset_deg < 0.0


def test_runtime_marker_hidden_at_low_speed() -> None:
    marker = FlightPathMarker().calculate(
        track_deg=90.0,
        heading_deg=90.0,
        ground_speed_kt=10.0,
        vertical_speed_fpm=0.0,
    )

    assert marker.valid is False