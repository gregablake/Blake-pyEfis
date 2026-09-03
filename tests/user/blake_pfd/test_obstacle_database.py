from pathlib import Path

import pytest

from pyefis.user.blake_pfd.faa_obstacle_csv import (
    FaaObstacleCsvError,
)
from pyefis.user.blake_pfd.obstacle_database import (
    ObstacleDatabase,
    ObstacleDatabaseBuilder,
)


HEADER = (
    "OAS,VERIFIED STATUS,COUNTRY,STATE,CITY,"
    "LATDEC,LONDEC,DMSLAT,DMSLON,TYPE,"
    "QUANTITY,AGL,AMSL,LIGHTING,ACCURACY,"
    "MARKING,FAA STUDY,ACTION,JDATE\n"
)


def row(
    *,
    ident: str,
    status: str = "O",
    lat_deg: float,
    lon_deg: float,
    agl_ft: int = 500,
    amsl_ft: int = 1200,
) -> str:
    return (
        f"{ident},{status},US,OH,CINCINNATI,"
        f"{lat_deg:.6f},{lon_deg:.6f},"
        ",,TOWER,1,"
        f"{agl_ft:05d},{amsl_ft:05d},"
        "R,5D,M,TEST,C,2026001\n"
    )


def write_source(
    path: Path,
    rows: list[str],
) -> None:
    path.write_text(
        HEADER
        + "".join(rows),
        encoding="cp1252",
    )


def test_builder_imports_only_verified_records(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DOF.CSV"
    database = tmp_path / "obstacles.sqlite"

    write_source(
        source,
        [
            row(
                ident="VERIFIED",
                lat_deg=39.01,
                lon_deg=-84.0,
            ),
            row(
                ident="UNVERIFIED",
                status="U",
                lat_deg=39.02,
                lon_deg=-84.0,
            ),
        ],
    )

    count = ObstacleDatabaseBuilder().build(
        source,
        database,
    )

    assert count == 1
    assert database.is_file()

    candidates = (
        ObstacleDatabase(database)
        .query_candidates(
            aircraft_lat_deg=39.0,
            aircraft_lon_deg=-84.0,
            max_distance_nm=10.0,
        )
    )

    assert candidates is not None
    assert [
        obstacle.ident
        for obstacle in candidates
    ] == [
        "VERIFIED"
    ]


def test_query_filters_far_obstacles(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DOF.CSV"
    database = tmp_path / "obstacles.sqlite"

    write_source(
        source,
        [
            row(
                ident="NEAR",
                lat_deg=39.01,
                lon_deg=-84.0,
            ),
            row(
                ident="FAR",
                lat_deg=40.0,
                lon_deg=-84.0,
            ),
        ],
    )

    ObstacleDatabaseBuilder().build(
        source,
        database,
    )

    candidates = (
        ObstacleDatabase(database)
        .query_candidates(
            aircraft_lat_deg=39.0,
            aircraft_lon_deg=-84.0,
            max_distance_nm=10.0,
        )
    )

    assert candidates is not None

    assert [
        obstacle.ident
        for obstacle in candidates
    ] == [
        "NEAR"
    ]


def test_missing_database_fails_closed(
    tmp_path: Path,
) -> None:
    state = (
        ObstacleDatabase(
            tmp_path
            / "missing.sqlite"
        )
        .query_candidates(
            aircraft_lat_deg=39.0,
            aircraft_lon_deg=-84.0,
            max_distance_nm=10.0,
        )
    )

    assert state is None


def test_invalid_query_fails_closed(
    tmp_path: Path,
) -> None:
    database = (
        tmp_path
        / "obstacles.sqlite"
    )

    result = (
        ObstacleDatabase(database)
        .query_candidates(
            aircraft_lat_deg=float(
                "nan"
            ),
            aircraft_lon_deg=-84.0,
            max_distance_nm=10.0,
        )
    )

    assert result is None


def test_failed_rebuild_preserves_existing_database(
    tmp_path: Path,
) -> None:
    valid_source = (
        tmp_path
        / "valid.csv"
    )

    invalid_source = (
        tmp_path
        / "invalid.csv"
    )

    database = (
        tmp_path
        / "obstacles.sqlite"
    )

    write_source(
        valid_source,
        [
            row(
                ident="KEEP",
                lat_deg=39.01,
                lon_deg=-84.0,
            )
        ],
    )

    builder = (
        ObstacleDatabaseBuilder()
    )

    builder.build(
        valid_source,
        database,
    )

    invalid_source.write_text(
        "OAS,LATDEC,LONDEC\n"
        "BAD,39.0,-84.0\n",
        encoding="cp1252",
    )

    with pytest.raises(
        FaaObstacleCsvError
    ):
        builder.build(
            invalid_source,
            database,
        )

    candidates = (
        ObstacleDatabase(database)
        .query_candidates(
            aircraft_lat_deg=39.0,
            aircraft_lon_deg=-84.0,
            max_distance_nm=10.0,
        )
    )

    assert candidates is not None

    assert [
        obstacle.ident
        for obstacle in candidates
    ] == [
        "KEEP"
    ]

    assert not Path(
        str(database)
        + ".tmp"
    ).exists()


def test_stale_source_database_fails_closed(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DOF.CSV"
    database = tmp_path / "obstacles.sqlite"

    write_source(
        source,
        [
            row(
                ident="STALE",
                lat_deg=39.01,
                lon_deg=-84.0,
            )
        ],
    )

    ObstacleDatabaseBuilder().build(
        source,
        database,
    )

    result = ObstacleDatabase(
        database,
        max_age_days=30.0,
        now_provider=lambda: (
            source.stat().st_mtime
            + 31.0 * 86400.0
        ),
    ).query_candidates(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        max_distance_nm=10.0,
    )

    assert result is None


def test_wrong_schema_version_fails_closed(
    tmp_path: Path,
) -> None:
    import sqlite3

    source = tmp_path / "DOF.CSV"
    database = tmp_path / "obstacles.sqlite"

    write_source(
        source,
        [
            row(
                ident="TEST",
                lat_deg=39.01,
                lon_deg=-84.0,
            )
        ],
    )

    ObstacleDatabaseBuilder().build(
        source,
        database,
    )

    with sqlite3.connect(
        database
    ) as connection:
        connection.execute(
            """
            UPDATE metadata
            SET value = '999'
            WHERE key = 'schema_version'
            """
        )

        connection.commit()

    result = ObstacleDatabase(
        database
    ).query_candidates(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        max_distance_nm=10.0,
    )

    assert result is None


def test_record_count_mismatch_fails_closed(
    tmp_path: Path,
) -> None:
    import sqlite3

    source = tmp_path / "DOF.CSV"
    database = tmp_path / "obstacles.sqlite"

    write_source(
        source,
        [
            row(
                ident="TEST",
                lat_deg=39.01,
                lon_deg=-84.0,
            )
        ],
    )

    ObstacleDatabaseBuilder().build(
        source,
        database,
    )

    with sqlite3.connect(
        database
    ) as connection:
        connection.execute(
            """
            UPDATE metadata
            SET value = '999'
            WHERE key = 'record_count'
            """
        )

        connection.commit()

    result = ObstacleDatabase(
        database
    ).query_candidates(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        max_distance_nm=10.0,
    )

    assert result is None


def test_tilde_database_path_expands(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"

    data_directory = (
        home
        / ".local"
        / "share"
        / "blake_pyefis"
    )

    data_directory.mkdir(
        parents=True
    )

    source = tmp_path / "DOF.CSV"

    database = (
        data_directory
        / "obstacles.sqlite"
    )

    write_source(
        source,
        [
            row(
                ident="HOME",
                lat_deg=39.01,
                lon_deg=-84.0,
            )
        ],
    )

    ObstacleDatabaseBuilder().build(
        source,
        database,
    )

    monkeypatch.setenv(
        "HOME",
        str(home),
    )

    result = ObstacleDatabase(
        "~/.local/share/blake_pyefis/obstacles.sqlite"
    ).query_candidates(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        max_distance_nm=10.0,
    )

    assert result is not None

    assert [
        obstacle.ident
        for obstacle in result
    ] == [
        "HOME"
    ]
