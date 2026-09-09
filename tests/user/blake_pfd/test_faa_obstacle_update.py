from __future__ import annotations

import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from pyefis.user.blake_pfd.faa_obstacle_update import (
    DAILY_DOF_URL,
    FaaObstacleUpdateError,
    FaaObstacleUpdater,
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


def obstacle_row(
    ident: str = "TEST",
) -> str:
    return (
        f"{ident},O,US,OH,CINCINNATI,"
        "39.010000,-84.000000,,,TOWER,1,"
        "00500,01200,R,5D,M,TEST,C,2026252\n"
    )


def make_zip(
    *,
    csv_name: str = "DOF.CSV",
    csv_text: str | None = None,
) -> bytes:
    if csv_text is None:
        csv_text = (
            HEADER
            + obstacle_row()
        )

    buffer = io.BytesIO()

    with ZipFile(
        buffer,
        "w",
        compression=ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            csv_name,
            csv_text.encode(
                "cp1252"
            ),
        )

    return buffer.getvalue()


class FakeResponse:
    def __init__(
        self,
        payload: bytes,
        *,
        last_modified: str | None,
    ) -> None:
        self._payload = payload
        self.headers = {}

        if last_modified is not None:
            self.headers[
                "Last-Modified"
            ] = last_modified

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        return None


def test_successful_update_uses_faa_last_modified(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "obstacles.sqlite"
    )

    last_modified = (
        "Wed, 09 Sep 2026 "
        "03:31:53 GMT"
    )

    expected_epoch = (
        datetime(
            2026,
            9,
            9,
            3,
            31,
            53,
            tzinfo=timezone.utc,
        ).timestamp()
    )

    seen_urls = []
    seen_headers = []

    def opener(request):
        seen_urls.append(
            request.full_url
        )

        seen_headers.append(
            dict(
                request.header_items()
            )
        )

        return FakeResponse(
            make_zip(),
            last_modified=(
                last_modified
            ),
        )

    updater = FaaObstacleUpdater(
        opener=opener,
    )

    count = updater.update(
        database_path
    )

    assert count == 1
    assert database_path.is_file()

    assert len(seen_urls) == 1
    assert (
        seen_urls[0]
        .startswith(
            DAILY_DOF_URL
        )
    )
    assert "cb=" in seen_urls[0]

    headers = {
        key.lower(): value
        for key, value
        in seen_headers[0].items()
    }

    assert (
        headers[
            "cache-control"
        ]
        == "no-cache"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        metadata = dict(
            connection.execute(
                """
                SELECT key, value
                FROM metadata
                """
            ).fetchall()
        )

    assert (
        float(
            metadata[
                "source_mtime_epoch_s"
            ]
        )
        == pytest.approx(
            expected_epoch
        )
    )

    candidates = (
        ObstacleDatabase(
            database_path,
            now_provider=lambda: (
                expected_epoch
            ),
        )
        .query_candidates(
            aircraft_lat_deg=39.0,
            aircraft_lon_deg=-84.0,
            max_distance_nm=10.0,
        )
    )

    assert candidates is not None
    assert [
        obstacle.ident
        for obstacle
        in candidates
    ] == [
        "TEST"
    ]


def test_missing_last_modified_fails_closed(
    tmp_path: Path,
) -> None:
    updater = FaaObstacleUpdater(
        opener=lambda request: (
            FakeResponse(
                make_zip(),
                last_modified=None,
            )
        )
    )

    database_path = (
        tmp_path
        / "obstacles.sqlite"
    )

    with pytest.raises(
        FaaObstacleUpdateError
    ):
        updater.update(
            database_path
        )

    assert not database_path.exists()


def test_invalid_last_modified_fails_closed(
    tmp_path: Path,
) -> None:
    updater = FaaObstacleUpdater(
        opener=lambda request: (
            FakeResponse(
                make_zip(),
                last_modified=(
                    "not-a-date"
                ),
            )
        )
    )

    database_path = (
        tmp_path
        / "obstacles.sqlite"
    )

    with pytest.raises(
        FaaObstacleUpdateError
    ):
        updater.update(
            database_path
        )

    assert not database_path.exists()


def test_missing_dof_csv_fails_closed(
    tmp_path: Path,
) -> None:
    updater = FaaObstacleUpdater(
        opener=lambda request: (
            FakeResponse(
                make_zip(
                    csv_name=(
                        "WRONG.CSV"
                    )
                ),
                last_modified=(
                    "Wed, 09 Sep 2026 "
                    "03:31:53 GMT"
                ),
            )
        )
    )

    database_path = (
        tmp_path
        / "obstacles.sqlite"
    )

    with pytest.raises(
        FaaObstacleUpdateError
    ):
        updater.update(
            database_path
        )

    assert not database_path.exists()


def test_failed_update_preserves_existing_database(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "old.csv"
    )

    source.write_text(
        HEADER
        + obstacle_row(
            ident="KEEP"
        ),
        encoding="cp1252",
    )

    database_path = (
        tmp_path
        / "obstacles.sqlite"
    )

    ObstacleDatabaseBuilder().build(
        source,
        database_path,
    )

    updater = FaaObstacleUpdater(
        opener=lambda request: (
            FakeResponse(
                b"not a zip",
                last_modified=(
                    "Wed, 09 Sep 2026 "
                    "03:31:53 GMT"
                ),
            )
        )
    )

    with pytest.raises(
        FaaObstacleUpdateError
    ):
        updater.update(
            database_path
        )

    candidates = (
        ObstacleDatabase(
            database_path,
            max_age_days=3650.0,
        )
        .query_candidates(
            aircraft_lat_deg=39.0,
            aircraft_lon_deg=-84.0,
            max_distance_nm=10.0,
        )
    )

    assert candidates is not None

    assert [
        obstacle.ident
        for obstacle
        in candidates
    ] == [
        "KEEP"
    ]
