import pytest

from pyefis.user.blake_pfd.core.map_airport_selector import (
    MapAirportMarker,
    MapAirportSelector,
)


def build_marker(
    identifier: str,
    x: float,
    y: float,
) -> MapAirportMarker:
    return MapAirportMarker(
        identifier=identifier,
        screen_x=x,
        screen_y=y,
        distance_nm=12.5,
        bearing_deg=90.0,
        name="Test Airport",
    )


def test_starts_without_selection() -> None:
    selector = MapAirportSelector()

    assert selector.selection.selected is False
    assert selector.selection.identifier is None


def test_touch_selects_airport() -> None:
    selector = MapAirportSelector()

    marker = build_marker(
        "KHAO",
        400.0,
        250.0,
    )

    selection = selector.select_at(
        point_x=405.0,
        point_y=255.0,
        markers=[marker],
    )

    assert selection.selected is True
    assert selection.identifier == "KHAO"
    assert selection.distance_nm == 12.5
    assert selection.bearing_deg == 90.0


def test_touch_radius_is_generous_for_cockpit_use() -> None:
    selector = MapAirportSelector(
        touch_radius_px=35.0,
    )

    marker = build_marker(
        "KCVG",
        500.0,
        300.0,
    )

    selection = selector.select_at(
        point_x=525.0,
        point_y=300.0,
        markers=[marker],
    )

    assert selection.identifier == "KCVG"


def test_touch_outside_radius_selects_nothing() -> None:
    selector = MapAirportSelector(
        touch_radius_px=30.0,
    )

    marker = build_marker(
        "KLUK",
        400.0,
        250.0,
    )

    selection = selector.select_at(
        point_x=500.0,
        point_y=350.0,
        markers=[marker],
    )

    assert selection.selected is False


def test_nearest_marker_wins() -> None:
    selector = MapAirportSelector(
        touch_radius_px=50.0,
    )

    markers = [
        build_marker(
            "KAAA",
            400.0,
            250.0,
        ),
        build_marker(
            "KBBB",
            420.0,
            250.0,
        ),
    ]

    selection = selector.select_at(
        point_x=418.0,
        point_y=250.0,
        markers=markers,
    )

    assert selection.identifier == "KBBB"


def test_selection_can_be_cleared() -> None:
    selector = MapAirportSelector()

    selector.select_at(
        point_x=400.0,
        point_y=250.0,
        markers=[
            build_marker(
                "KHAO",
                400.0,
                250.0,
            )
        ],
    )

    selection = selector.clear()

    assert selection.selected is False
    assert selection.identifier is None


def test_invalid_touch_clears_selection() -> None:
    selector = MapAirportSelector()

    selection = selector.select_at(
        point_x="bad",
        point_y=250.0,
        markers=[],
    )

    assert selection.selected is False


def test_identifier_is_normalized_uppercase() -> None:
    selector = MapAirportSelector()

    selection = selector.select_at(
        point_x=100.0,
        point_y=100.0,
        markers=[
            build_marker(
                "khao",
                100.0,
                100.0,
            )
        ],
    )

    assert selection.identifier == "KHAO"


def test_constructor_rejects_bad_radius() -> None:
    with pytest.raises(ValueError):
        MapAirportSelector(
            touch_radius_px=0.0,
        )

    with pytest.raises(ValueError):
        MapAirportSelector(
            touch_radius_px=-1.0,
        )