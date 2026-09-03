from pyefis.user.blake_pfd.obstacle_runtime import (
    ObstacleRuntimeProvider,
)
from pyefis.user.blake_pfd.obstacles import (
    Obstacle,
)


class FakeObstacleDatabase:
    def __init__(
        self,
        obstacles=(),
    ) -> None:
        self.obstacles = tuple(
            obstacles
        )

        self.calls: list[
            tuple[
                float,
                float,
                float,
            ]
        ] = []

        self.fail = False

    def query_candidates(
        self,
        *,
        aircraft_lat_deg: float,
        aircraft_lon_deg: float,
        max_distance_nm: float,
    ):
        self.calls.append(
            (
                aircraft_lat_deg,
                aircraft_lon_deg,
                max_distance_nm,
            )
        )

        if self.fail:
            return None

        return self.obstacles


def obstacle_at(
    *,
    ident: str,
    lat_deg: float,
) -> Obstacle:
    return Obstacle(
        ident=ident,
        lat_deg=lat_deg,
        lon_deg=-84.0,
        elevation_ft=1200.0,
        height_agl_ft=500.0,
    )


def test_first_update_queries_with_buffer() -> None:
    database = FakeObstacleDatabase()

    provider = ObstacleRuntimeProvider(
        database,
        max_distance_nm=10.0,
        refresh_distance_nm=1.0,
    )

    state = provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert state.ok is True
    assert len(database.calls) == 1

    assert (
        database.calls[0][2]
        == 11.0
    )


def test_small_movement_reuses_cached_candidates() -> None:
    database = FakeObstacleDatabase()

    provider = ObstacleRuntimeProvider(
        database,
    )

    provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    provider.update(
        aircraft_lat=39.005,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert len(database.calls) == 1


def test_one_nm_movement_refreshes_database() -> None:
    database = FakeObstacleDatabase()

    provider = ObstacleRuntimeProvider(
        database,
    )

    provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    provider.update(
        aircraft_lat=39.02,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert len(database.calls) == 2


def test_buffer_catches_obstacle_entering_live_range() -> None:
    # About 10.5 NM north of the original
    # query center.
    obstacle = obstacle_at(
        ident="ENTERING",
        lat_deg=(
            39.0
            + 10.5 / 60.0
        ),
    )

    database = FakeObstacleDatabase(
        [obstacle]
    )

    provider = ObstacleRuntimeProvider(
        database,
        max_distance_nm=10.0,
        refresh_distance_nm=1.0,
    )

    original = provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert original.nearby == []

    # Move about 0.8 NM toward it.
    moved = provider.update(
        aircraft_lat=(
            39.0
            + 0.8 / 60.0
        ),
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    # No database refresh yet.
    assert len(database.calls) == 1

    assert moved.nearby is not None

    assert [
        item.ident
        for item in moved.nearby
    ] == [
        "ENTERING"
    ]


def test_query_failure_clears_cached_data() -> None:
    database = FakeObstacleDatabase(
        [
            obstacle_at(
                ident="OLD",
                lat_deg=39.01,
            )
        ]
    )

    provider = ObstacleRuntimeProvider(
        database,
    )

    first = provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert first.ok is True
    assert first.nearby

    database.fail = True

    failed = provider.update(
        aircraft_lat=39.02,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert failed.ok is False
    assert failed.nearby == []
    assert failed.warning is False


def test_repeated_update_inside_interval_reuses_state() -> None:
    now = [100.0]

    database = FakeObstacleDatabase(
        [
            obstacle_at(
                ident="CACHED",
                lat_deg=39.01,
            )
        ]
    )

    provider = ObstacleRuntimeProvider(
        database,
        now_provider=lambda: now[0],
    )

    first = provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    second = provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert second is first


def test_elapsed_interval_recalculates_state() -> None:
    now = [100.0]

    database = FakeObstacleDatabase(
        [
            obstacle_at(
                ident="TIMED",
                lat_deg=39.01,
            )
        ]
    )

    provider = ObstacleRuntimeProvider(
        database,
        evaluation_interval_s=0.10,
        now_provider=lambda: now[0],
    )

    first = provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    now[0] += 0.11

    second = provider.update(
        aircraft_lat=39.0,
        aircraft_lon=-84.0,
        aircraft_alt_ft=3000.0,
    )

    assert second is not first
