from pyefis.user.blake_pfd.core.map_airport_selector import (
    MapAirportMarker,
    MapAirportSelector,
)


def test_rendered_marker_can_be_selected() -> None:
    selector = MapAirportSelector(
        touch_radius_px=35.0,
    )

    marker = MapAirportMarker(
        identifier="KHAO",
        name="Butler County Regional",
        distance_nm=11.5,
        bearing_deg=25.0,
        screen_x=500.0,
        screen_y=300.0,
    )

    selection = selector.select_at(
        point_x=510.0,
        point_y=305.0,
        markers=[marker],
    )

    assert selection.selected is True
    assert selection.identifier == "KHAO"
    assert selection.name == "Butler County Regional"


def test_panned_marker_uses_display_position() -> None:
    selector = MapAirportSelector(
        touch_radius_px=35.0,
    )

    original_x = 400.0
    original_y = 250.0

    offset_x = 80.0
    offset_y = -30.0

    marker = MapAirportMarker(
        identifier="KCVG",
        name="Cincinnati Northern Kentucky",
        distance_nm=20.0,
        bearing_deg=180.0,
        screen_x=(
            original_x
            + offset_x
        ),
        screen_y=(
            original_y
            + offset_y
        ),
    )

    selection = selector.select_at(
        point_x=480.0,
        point_y=220.0,
        markers=[marker],
    )

    assert selection.identifier == "KCVG"


def test_touching_empty_map_clears_selection() -> None:
    selector = MapAirportSelector()

    marker = MapAirportMarker(
        identifier="KLUK",
        name="Lunken",
        distance_nm=5.0,
        bearing_deg=90.0,
        screen_x=400.0,
        screen_y=300.0,
    )

    selector.select_at(
        point_x=400.0,
        point_y=300.0,
        markers=[marker],
    )

    selection = selector.select_at(
        point_x=100.0,
        point_y=100.0,
        markers=[marker],
    )

    assert selection.selected is False