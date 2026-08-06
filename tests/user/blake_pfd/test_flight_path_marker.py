from pyefis.user.blake_pfd.core.flight_path_marker import (
    FlightPathMarker,
)


def test_level_flight():

    marker = FlightPathMarker().calculate(
        track_deg=90,
        heading_deg=90,
        ground_speed_kt=100,
        vertical_speed_fpm=0,
    )

    assert marker.valid
    assert marker.flight_path_angle_deg == 0


def test_climb():

    marker = FlightPathMarker().calculate(
        track_deg=90,
        heading_deg=90,
        ground_speed_kt=120,
        vertical_speed_fpm=1000,
    )

    assert marker.flight_path_angle_deg > 0


def test_low_speed_invalid():

    marker = FlightPathMarker().calculate(
        track_deg=90,
        heading_deg=90,
        ground_speed_kt=10,
        vertical_speed_fpm=0,
    )

    assert marker.valid is False