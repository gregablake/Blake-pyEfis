from math import isclose

from pyefis.user.blake_pfd.core.runway_geometry import (
    RunwayEndpointGeometry,
    RunwayGeometry,
)
from pyefis.user.blake_pfd.core.safe_taxi_projection import (
    SafeTaxiMapProjector,
)


def endpoint(
    ident,
    *,
    north_ft,
    east_ft,
):
    return RunwayEndpointGeometry(
        ident=ident,
        north_ft=north_ft,
        east_ft=east_ft,
        up_ft=0.0,
        distance_ft=(
            north_ft ** 2
            + east_ft ** 2
        ) ** 0.5,
        bearing_deg=0.0,
        elevation_ft=633.0,
    )


def runway(
    *,
    low_north=-500.0,
    low_east=0.0,
    high_north=500.0,
    high_east=0.0,
    width_ft=100.0,
):
    return RunwayGeometry(
        airport_ident="KHAO",
        length_ft=1000.0,
        width_ft=width_ft,
        low_end=endpoint(
            "11",
            north_ft=low_north,
            east_ft=low_east,
        ),
        high_end=endpoint(
            "29",
            north_ft=high_north,
            east_ft=high_east,
        ),
    )


def test_ownship_is_fixed_at_screen_center():
    projector = SafeTaxiMapProjector(
        range_ft=1000.0,
    )

    state = projector.project(
        runways=[runway()],
        heading_deg=0.0,
        width_px=1000,
        height_px=600,
    )

    assert state.valid is True
    assert state.ownship_x == 500.0
    assert state.ownship_y == 300.0


def test_north_up_runway_projects_vertically():
    projector = SafeTaxiMapProjector(
        range_ft=1000.0,
    )

    state = projector.project(
        runways=[runway()],
        heading_deg=0.0,
        width_px=1000,
        height_px=600,
    )

    projected = state.runways[0]

    assert isclose(
        projected.low_center_x,
        500.0,
        abs_tol=0.01,
    )
    assert isclose(
        projected.high_center_x,
        500.0,
        abs_tol=0.01,
    )

    assert projected.low_center_y > 300.0
    assert projected.high_center_y < 300.0


def test_heading_90_rotates_north_runway_horizontal():
    projector = SafeTaxiMapProjector(
        range_ft=1000.0,
    )

    state = projector.project(
        runways=[runway()],
        heading_deg=90.0,
        width_px=1000,
        height_px=600,
    )

    projected = state.runways[0]

    assert isclose(
        projected.low_center_y,
        300.0,
        abs_tol=0.01,
    )
    assert isclose(
        projected.high_center_y,
        300.0,
        abs_tol=0.01,
    )

    assert projected.low_center_x > 500.0
    assert projected.high_center_x < 500.0


def test_runway_width_is_preserved():
    projector = SafeTaxiMapProjector(
        range_ft=1000.0,
    )

    state = projector.project(
        runways=[runway(width_ft=100.0)],
        heading_deg=0.0,
        width_px=1000,
        height_px=600,
    )

    projected = state.runways[0]

    # 600 px represents 2000 ft.
    # A 100 ft runway therefore spans 30 px.
    xs = [
        point.x
        for point in projected.corners
    ]

    assert isclose(
        max(xs) - min(xs),
        30.0,
        abs_tol=0.01,
    )


def test_multiple_runways_are_projected():
    projector = SafeTaxiMapProjector(
        range_ft=2000.0,
    )

    state = projector.project(
        runways=[
            runway(),
            runway(
                low_north=0.0,
                low_east=-700.0,
                high_north=0.0,
                high_east=700.0,
                width_ft=75.0,
            ),
        ],
        heading_deg=0.0,
        width_px=1000,
        height_px=600,
    )

    assert state.valid is True
    assert len(state.runways) == 2


def test_invalid_heading_fails_closed():
    projector = SafeTaxiMapProjector(
        range_ft=1000.0,
    )

    state = projector.project(
        runways=[runway()],
        heading_deg=float("nan"),
        width_px=1000,
        height_px=600,
    )

    assert state.valid is False
    assert state.runways == ()


def test_invalid_screen_dimensions_fail_closed():
    projector = SafeTaxiMapProjector(
        range_ft=1000.0,
    )

    state = projector.project(
        runways=[runway()],
        heading_deg=0.0,
        width_px=0,
        height_px=600,
    )

    assert state.valid is False
    assert state.runways == ()


def test_bad_runway_is_skipped_without_losing_good_runway():
    projector = SafeTaxiMapProjector(
        range_ft=1000.0,
    )

    good = runway()

    bad = runway(
        low_north=0.0,
        low_east=0.0,
        high_north=0.0,
        high_east=0.0,
    )

    state = projector.project(
        runways=[bad, good],
        heading_deg=0.0,
        width_px=1000,
        height_px=600,
    )

    assert state.valid is True
    assert len(state.runways) == 1
