from __future__ import annotations

from math import nan

import pytest

from pyefis.user.blake_pfd.core.obstacle_projection import (
    ObstacleProjectionComputer,
)
from pyefis.user.blake_pfd.obstacles import (
    Obstacle,
)


def make_obstacle(
    *,
    ident: str = "TEST",
    distance_nm: float = 1.0,
    bearing_deg: float = 0.0,
    elevation_ft: float = 1000.0,
) -> Obstacle:
    return Obstacle(
        ident=ident,
        lat_deg=39.0,
        lon_deg=-84.0,
        elevation_ft=elevation_ft,
        height_agl_ft=300.0,
        distance_nm=distance_nm,
        bearing_deg=bearing_deg,
    )


def test_obstacle_ahead_projects_to_screen_center():
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                bearing_deg=0.0,
                elevation_ft=1000.0,
            )
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    assert len(result) == 1

    point = result[0]

    assert point.ident == "TEST"

    assert (
        point.x_px
        == pytest.approx(
            512.0,
            abs=1.0,
        )
    )

    assert (
        point.y_px
        == pytest.approx(
            300.0,
            abs=1.0,
        )
    )


def test_obstacle_right_of_heading_projects_right():
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                bearing_deg=20.0,
            )
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    assert len(result) == 1

    assert (
        result[0].x_px
        > 512.0
    )


def test_obstacle_below_aircraft_projects_below_center():
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                elevation_ft=500.0,
            )
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    assert len(result) == 1

    assert (
        result[0].y_px
        > 300.0
    )


def test_pitch_up_moves_obstacle_down():
    projector = ObstacleProjectionComputer()

    level = projector.project(
        obstacles=[
            make_obstacle()
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    pitched = projector.project(
        obstacles=[
            make_obstacle()
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=10.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    assert len(level) == 1
    assert len(pitched) == 1

    assert (
        pitched[0].y_px
        > level[0].y_px
    )


def test_obstacle_behind_aircraft_is_not_returned():
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                bearing_deg=180.0,
            )
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    assert result == []


def test_offscreen_obstacle_is_not_returned():
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                bearing_deg=80.0,
            )
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    assert result == []


def test_invalid_obstacle_is_skipped_without_losing_good_one():
    projector = ObstacleProjectionComputer()

    bad = make_obstacle(
        ident="BAD",
        distance_nm=nan,
    )

    good = make_obstacle(
        ident="GOOD",
    )

    result = projector.project(
        obstacles=[
            bad,
            good,
        ],
        aircraft_alt_ft=1000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
    )

    assert len(result) == 1
    assert result[0].ident == "GOOD"


@pytest.mark.parametrize(
    (
        "aircraft_alt_ft",
        "heading_deg",
        "pitch_deg",
        "roll_deg",
        "width_px",
        "height_px",
    ),
    [
        (
            nan,
            0.0,
            0.0,
            0.0,
            1024,
            600,
        ),
        (
            1000.0,
            nan,
            0.0,
            0.0,
            1024,
            600,
        ),
        (
            1000.0,
            0.0,
            nan,
            0.0,
            1024,
            600,
        ),
        (
            1000.0,
            0.0,
            0.0,
            nan,
            1024,
            600,
        ),
        (
            1000.0,
            0.0,
            0.0,
            0.0,
            0,
            600,
        ),
        (
            1000.0,
            0.0,
            0.0,
            0.0,
            1024,
            0,
        ),
    ],
)
def test_invalid_projection_inputs_fail_closed(
    aircraft_alt_ft,
    heading_deg,
    pitch_deg,
    roll_deg,
    width_px,
    height_px,
):
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle()
        ],
        aircraft_alt_ft=aircraft_alt_ft,
        heading_deg=heading_deg,
        pitch_deg=pitch_deg,
        roll_deg=roll_deg,
        width_px=width_px,
        height_px=height_px,
    )

    assert result == []


def test_projected_obstacle_is_individually_marked_threat():
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                distance_nm=2.0,
                elevation_ft=1500.0,
            )
        ],
        aircraft_alt_ft=2000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
        warning_distance_nm=3.0,
        warning_clearance_ft=1000.0,
    )

    assert len(result) == 1
    assert result[0].threat is True


def test_projected_obstacle_with_safe_clearance_is_not_threat():
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                distance_nm=2.0,
                elevation_ft=500.0,
            )
        ],
        aircraft_alt_ft=2000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
        warning_distance_nm=3.0,
        warning_clearance_ft=1000.0,
    )

    assert len(result) == 1
    assert result[0].threat is False


@pytest.mark.parametrize(
    (
        "distance_nm",
        "elevation_ft",
    ),
    [
        (
            3.0,
            1500.0,
        ),
        (
            2.0,
            1000.0,
        ),
    ],
)
def test_threat_threshold_boundaries_are_not_inclusive(
    distance_nm,
    elevation_ft,
):
    projector = ObstacleProjectionComputer()

    result = projector.project(
        obstacles=[
            make_obstacle(
                distance_nm=distance_nm,
                elevation_ft=elevation_ft,
            )
        ],
        aircraft_alt_ft=2000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1024,
        height_px=600,
        warning_distance_nm=3.0,
        warning_clearance_ft=1000.0,
    )

    assert len(result) == 1
    assert result[0].threat is False
