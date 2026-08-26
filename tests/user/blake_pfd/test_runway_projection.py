from __future__ import annotations

from pyefis.user.blake_pfd.core.runway_geometry import (
    RunwayEndpointGeometry,
    RunwayGeometry,
)

from pyefis.user.blake_pfd.core.runway_projection import (
    ProjectedRunway,
    RunwayProjectionComputer,
)
from pyefis.user.blake_pfd.core.synthetic_camera import (
    ProjectedPoint,
)


def runway_ahead() -> RunwayGeometry:
    return RunwayGeometry(
        airport_ident="TEST",
        length_ft=5000.0,
        width_ft=100.0,
        low_end=RunwayEndpointGeometry(
            ident="18",
            north_ft=3000.0,
            east_ft=0.0,
            up_ft=-500.0,
            distance_ft=3000.0,
            bearing_deg=0.0,
            elevation_ft=500.0,
        ),
        high_end=RunwayEndpointGeometry(
            ident="36",
            north_ft=8000.0,
            east_ft=0.0,
            up_ft=-500.0,
            distance_ft=8000.0,
            bearing_deg=0.0,
            elevation_ft=500.0,
        ),
    )


def test_runway_ahead_projects_to_visible_polygon() -> None:
    projected = RunwayProjectionComputer().project(
        geometry=runway_ahead(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected is not None
    assert projected.visible is True


def test_near_runway_end_appears_wider() -> None:
    projected = RunwayProjectionComputer().project(
        geometry=runway_ahead(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected is not None

    low_width = abs(
        projected.low_right.x_px
        - projected.low_left.x_px
    )

    high_width = abs(
        projected.high_right.x_px
        - projected.high_left.x_px
    )

    assert low_width > high_width


def test_runway_below_aircraft_projects_below_center() -> None:
    projected = RunwayProjectionComputer().project(
        geometry=runway_ahead(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected is not None

    assert projected.low_left.y_px > 360.0
    assert projected.low_right.y_px > 360.0


def test_pitch_up_moves_runway_farther_down() -> None:
    computer = RunwayProjectionComputer()

    level = computer.project(
        geometry=runway_ahead(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    nose_up = computer.project(
        geometry=runway_ahead(),
        heading_deg=0.0,
        pitch_deg=10.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert level is not None
    assert nose_up is not None

    assert (
        nose_up.low_left.y_px
        > level.low_left.y_px
    )


def test_zero_runway_width_fails_closed() -> None:
    geometry = runway_ahead()

    invalid = RunwayGeometry(
        airport_ident=geometry.airport_ident,
        length_ft=geometry.length_ft,
        width_ft=0.0,
        low_end=geometry.low_end,
        high_end=geometry.high_end,
    )

    projected = RunwayProjectionComputer().project(
        geometry=invalid,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected is None


def test_runway_behind_aircraft_is_not_visible() -> None:
    geometry = runway_ahead()

    projected = RunwayProjectionComputer().project(
        geometry=geometry,
        heading_deg=180.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected is not None
    assert projected.visible is False


def test_partial_runway_projection_fails_closed() -> None:
    visible = ProjectedPoint(
        x_px=640.0,
        y_px=400.0,
        visible=True,
    )

    hidden = ProjectedPoint(
        x_px=0.0,
        y_px=0.0,
        visible=False,
    )

    projected = ProjectedRunway(
        low_left=visible,
        low_right=visible,
        high_left=visible,
        high_right=hidden,
    )

    assert projected.visible is False
