from pathlib import Path

import pytest

from pyefis.user.blake_pfd.faa_obstacle_csv import (
    FaaObstacleCsvError,
    FaaObstacleCsvLoader,
)


HEADER = (
    "OAS,VERIFIED STATUS,COUNTRY,STATE,CITY,"
    "LATDEC,LONDEC,DMSLAT,DMSLON,TYPE,"
    "QUANTITY,AGL,AMSL,LIGHTING,ACCURACY,"
    "MARKING,FAA STUDY,ACTION,JDATE\n"
)


def write_csv(
    path: Path,
    rows: list[str],
) -> None:
    path.write_text(
        HEADER
        + "".join(rows),
        encoding="utf-8",
    )


def test_verified_faa_obstacle_loads(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    write_csv(
        path,
        [
            (
                "01-001307,O,US,AL,"
                "DAUPHIN ISLAND,"
                "30.179167,-88.077500,"
                "30 10 45.00N,"
                "088 04 39.00W,"
                "RIG,1,00236,00236,R,"
                "5D,M,1990ASO01578OE,"
                "C,2014138\n"
            )
        ],
    )

    obstacles = list(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    )

    assert len(obstacles) == 1

    obstacle = obstacles[0]

    assert obstacle.ident == "01-001307"
    assert obstacle.lat_deg == 30.179167
    assert obstacle.lon_deg == -88.0775
    assert obstacle.height_agl_ft == 236.0
    assert obstacle.elevation_ft == 236.0


def test_whitespace_is_removed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    write_csv(
        path,
        [
            (
                " 01-000001 , O ,US,OH,"
                "CINCINNATI,"
                "39.100000,-84.500000,"
                ",,TOWER,1,"
                "00500,01200,R,5D,M,"
                "TEST,C,2026001\n"
            )
        ],
    )

    obstacle = next(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    )

    assert obstacle.ident == "01-000001"
    assert obstacle.height_agl_ft == 500.0
    assert obstacle.elevation_ft == 1200.0


def test_unverified_obstacle_is_excluded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    write_csv(
        path,
        [
            (
                "01-000001,U,US,OH,"
                "CINCINNATI,"
                "39.100000,-84.500000,"
                ",,TOWER,1,"
                "00500,01200,R,,,"
                "TEST,C,2026001\n"
            )
        ],
    )

    assert list(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    ) == []


def test_dismantled_obstacle_is_excluded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    write_csv(
        path,
        [
            (
                "01-000001,O,US,OH,"
                "CINCINNATI,"
                "39.100000,-84.500000,"
                ",,TOWER,1,"
                "00500,01200,R,5D,M,"
                "TEST,D,2026001\n"
            )
        ],
    )

    assert list(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    ) == []


def test_invalid_coordinates_are_excluded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    write_csv(
        path,
        [
            (
                "01-000001,O,US,OH,"
                "CINCINNATI,"
                "999.0,-84.500000,"
                ",,TOWER,1,"
                "00500,01200,R,5D,M,"
                "TEST,C,2026001\n"
            )
        ],
    )

    assert list(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    ) == []


def test_missing_height_is_excluded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    write_csv(
        path,
        [
            (
                "01-000001,O,US,OH,"
                "CINCINNATI,"
                "39.100000,-84.500000,"
                ",,TOWER,1,"
                ",01200,R,5D,M,"
                "TEST,C,2026001\n"
            )
        ],
    )

    assert list(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    ) == []


def test_missing_required_header_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    path.write_text(
        "OAS,LATDEC,LONDEC\n"
        "01-000001,39.0,-84.0\n",
        encoding="utf-8",
    )

    with pytest.raises(
        FaaObstacleCsvError
    ):
        list(
            FaaObstacleCsvLoader()
            .iter_obstacles(path)
        )


def test_cp1252_text_is_supported(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    row = (
        "01-000002,O,US,OH,"
        "O\u2019BRIEN FIELD,"
        "39.100000,-84.500000,"
        ",,TOWER,1,"
        "00500,01200,R,5D,M,"
        "TEST,C,2026001\n"
    )

    path.write_text(
        HEADER + row,
        encoding="cp1252",
    )

    obstacles = list(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    )

    assert len(obstacles) == 1
    assert obstacles[0].ident == "01-000002"


def test_unknown_verification_status_is_excluded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "DOF.CSV"

    write_csv(
        path,
        [
            (
                "01-000003,V,US,OH,"
                "CINCINNATI,"
                "39.100000,-84.500000,"
                ",,TOWER,1,"
                "00500,01200,R,5D,M,"
                "TEST,C,2026001\n"
            )
        ],
    )

    assert list(
        FaaObstacleCsvLoader()
        .iter_obstacles(path)
    ) == []
