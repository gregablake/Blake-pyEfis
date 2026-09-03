from pyefis.user.blake_pfd.obstacles import (
    Obstacle,
    ObstacleComputer,
)


def obstacle_north(
    *,
    lat_deg: float = 39.0166667,
    elevation_ft: float = 1200.0,
) -> Obstacle:
    return Obstacle(
        ident="TEST",
        lat_deg=lat_deg,
        lon_deg=-84.0,
        elevation_ft=elevation_ft,
        height_agl_ft=500.0,
    )


def test_missing_database_reports_unavailable() -> None:
    state = ObstacleComputer().update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=2000.0,
    )

    assert state.ok is False
    assert state.nearby == []
    assert state.warning is False


def test_live_distance_and_bearing_are_computed() -> None:
    state = ObstacleComputer(
        [obstacle_north()]
    ).update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert state.ok is True
    assert state.nearby is not None
    assert len(state.nearby) == 1

    obstacle = state.nearby[0]

    assert 0.9 < obstacle.distance_nm < 1.1
    assert (
        obstacle.bearing_deg < 1.0
        or obstacle.bearing_deg > 359.0
    )


def test_near_obstacle_with_low_clearance_warns() -> None:
    state = ObstacleComputer(
        [obstacle_north()]
    ).update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=1800.0,
    )

    assert state.ok is True
    assert state.warning is True


def test_sufficient_vertical_clearance_does_not_warn() -> None:
    state = ObstacleComputer(
        [obstacle_north()]
    ).update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert state.ok is True
    assert state.warning is False


def test_far_obstacle_is_filtered_out() -> None:
    state = ObstacleComputer(
        [
            obstacle_north(
                lat_deg=40.0,
            )
        ]
    ).update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=1800.0,
    )

    assert state.ok is True
    assert state.nearby == []
    assert state.warning is False


def test_warning_obstacle_is_presented_first() -> None:
    safe_near = Obstacle(
        ident="SAFE",
        lat_deg=39.008,
        lon_deg=-84.0,
        elevation_ft=200.0,
        height_agl_ft=100.0,
    )

    warning_farther = Obstacle(
        ident="WARNING",
        lat_deg=39.016,
        lon_deg=-84.0,
        elevation_ft=1500.0,
        height_agl_ft=500.0,
    )

    state = ObstacleComputer(
        [
            safe_near,
            warning_farther,
        ]
    ).update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=2000.0,
    )

    assert state.warning is True
    assert state.nearby is not None
    assert state.nearby[0].ident == "WARNING"


def test_invalid_aircraft_position_fails_closed() -> None:
    state = ObstacleComputer(
        [obstacle_north()]
    ).update(
        aircraft_lat=float("nan"),
        aircraft_lon=-84.0,
        aircraft_alt_ft=2000.0,
    )

    assert state.ok is False
    assert state.nearby == []
    assert state.warning is False
