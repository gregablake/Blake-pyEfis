from __future__ import annotations

import sqlite3
from collections.abc import Callable
from math import (
    cos,
    isfinite,
    radians,
)
from pathlib import Path
from time import time

from pyefis.user.blake_pfd.faa_obstacle_csv import (
    FaaObstacleCsvLoader,
)
from pyefis.user.blake_pfd.obstacles import (
    Obstacle,
)


SCHEMA_VERSION = 1
INSERT_BATCH_SIZE = 5000


class ObstacleDatabaseBuilder:
    def __init__(
        self,
        loader: FaaObstacleCsvLoader | None = None,
    ) -> None:
        self.loader = (
            loader
            if loader is not None
            else FaaObstacleCsvLoader()
        )

    def build(
        self,
        source_csv: str | Path,
        database_path: str | Path,
    ) -> int:
        source_path = Path(
            source_csv
        )

        output_path = Path(
            database_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = Path(
            str(output_path)
            + ".tmp"
        )

        temporary_path.unlink(
            missing_ok=True
        )

        source_mtime_epoch_s = (
            source_path.stat().st_mtime
        )

        connection: (
            sqlite3.Connection
            | None
        ) = None

        try:
            connection = sqlite3.connect(
                temporary_path
            )

            # This database is being constructed in a
            # disposable temporary file. Durability is
            # provided by replacing the live database
            # only after a successful completed build.
            connection.execute(
                "PRAGMA journal_mode=OFF"
            )

            connection.execute(
                "PRAGMA synchronous=OFF"
            )

            connection.executescript(
                """
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE obstacles (
                    id INTEGER PRIMARY KEY,
                    ident TEXT NOT NULL,
                    lat_deg REAL NOT NULL,
                    lon_deg REAL NOT NULL,
                    elevation_ft REAL NOT NULL,
                    height_agl_ft REAL NOT NULL
                );
                """
            )

            insert_sql = """
                INSERT INTO obstacles (
                    ident,
                    lat_deg,
                    lon_deg,
                    elevation_ft,
                    height_agl_ft
                )
                VALUES (?, ?, ?, ?, ?)
            """

            batch: list[
                tuple[
                    str,
                    float,
                    float,
                    float,
                    float,
                ]
            ] = []

            record_count = 0

            for obstacle in (
                self.loader
                .iter_obstacles(
                    source_path
                )
            ):
                batch.append(
                    (
                        obstacle.ident,
                        obstacle.lat_deg,
                        obstacle.lon_deg,
                        obstacle.elevation_ft,
                        obstacle.height_agl_ft,
                    )
                )

                if (
                    len(batch)
                    >= INSERT_BATCH_SIZE
                ):
                    connection.executemany(
                        insert_sql,
                        batch,
                    )

                    record_count += len(
                        batch
                    )

                    batch.clear()

            if batch:
                connection.executemany(
                    insert_sql,
                    batch,
                )

                record_count += len(
                    batch
                )

            connection.execute(
                """
                CREATE INDEX
                obstacle_lat_lon_idx
                ON obstacles (
                    lat_deg,
                    lon_deg
                )
                """
            )

            connection.executemany(
                """
                INSERT INTO metadata (
                    key,
                    value
                )
                VALUES (?, ?)
                """,
                (
                    (
                        "schema_version",
                        str(
                            SCHEMA_VERSION
                        ),
                    ),
                    (
                        "record_count",
                        str(
                            record_count
                        ),
                    ),
                    (
                        "source_mtime_epoch_s",
                        str(
                            source_mtime_epoch_s
                        ),
                    ),
                ),
            )

            connection.commit()

            quick_check = (
                connection.execute(
                    "PRAGMA quick_check"
                ).fetchone()
            )

            if (
                quick_check is None
                or quick_check[0]
                != "ok"
            ):
                raise RuntimeError(
                    "Obstacle database "
                    "integrity check failed"
                )

            connection.close()
            connection = None

            temporary_path.replace(
                output_path
            )

            return record_count

        except Exception:
            if connection is not None:
                connection.close()

            temporary_path.unlink(
                missing_ok=True
            )

            raise


class ObstacleDatabase:
    def __init__(
        self,
        database_path: str | Path,
        *,
        max_age_days: float = 30.0,
        now_provider: Callable[
            [],
            float,
        ] = time,
    ) -> None:
        self.database_path = (
            Path(
                database_path
            )
            .expanduser()
        )

        self.max_age_days = float(
            max_age_days
        )

        self._now_provider = (
            now_provider
        )

    def query_candidates(
        self,
        *,
        aircraft_lat_deg: float,
        aircraft_lon_deg: float,
        max_distance_nm: float,
    ) -> tuple[
        Obstacle,
        ...,
    ] | None:
        if not self._query_valid(
            aircraft_lat_deg,
            aircraft_lon_deg,
            max_distance_nm,
        ):
            return None

        if not self.database_path.is_file():
            return None

        latitude_delta_deg = (
            max_distance_nm
            / 60.0
        )

        cosine_latitude = abs(
            cos(
                radians(
                    aircraft_lat_deg
                )
            )
        )

        if cosine_latitude < 1e-6:
            longitude_delta_deg = (
                180.0
            )
        else:
            longitude_delta_deg = min(
                180.0,
                max_distance_nm
                / (
                    60.0
                    * cosine_latitude
                ),
            )

        minimum_latitude = max(
            -90.0,
            aircraft_lat_deg
            - latitude_delta_deg,
        )

        maximum_latitude = min(
            90.0,
            aircraft_lat_deg
            + latitude_delta_deg,
        )

        minimum_longitude = (
            aircraft_lon_deg
            - longitude_delta_deg
        )

        maximum_longitude = (
            aircraft_lon_deg
            + longitude_delta_deg
        )

        try:
            connection = sqlite3.connect(
                self.database_path
            )

            try:
                if not self._database_valid(
                    connection
                ):
                    return None

                rows = self._query_rows(
                    connection,
                    minimum_latitude=(
                        minimum_latitude
                    ),
                    maximum_latitude=(
                        maximum_latitude
                    ),
                    minimum_longitude=(
                        minimum_longitude
                    ),
                    maximum_longitude=(
                        maximum_longitude
                    ),
                    longitude_delta_deg=(
                        longitude_delta_deg
                    ),
                )
            finally:
                connection.close()

        except sqlite3.Error:
            return None

        obstacles: list[
            Obstacle
        ] = []

        for row in rows:
            (
                ident,
                lat_deg,
                lon_deg,
                elevation_ft,
                height_agl_ft,
            ) = row

            if not (
                isinstance(
                    ident,
                    str,
                )
                and ident.strip()
                and all(
                    isfinite(value)
                    for value in (
                        lat_deg,
                        lon_deg,
                        elevation_ft,
                        height_agl_ft,
                    )
                )
            ):
                return None

            obstacles.append(
                Obstacle(
                    ident=ident,
                    lat_deg=float(
                        lat_deg
                    ),
                    lon_deg=float(
                        lon_deg
                    ),
                    elevation_ft=float(
                        elevation_ft
                    ),
                    height_agl_ft=float(
                        height_agl_ft
                    ),
                )
            )

        return tuple(
            obstacles
        )

    def _database_valid(
        self,
        connection: sqlite3.Connection,
    ) -> bool:
        if (
            not isfinite(
                self.max_age_days
            )
            or self.max_age_days <= 0.0
        ):
            return False

        rows = connection.execute(
            """
            SELECT key, value
            FROM metadata
            """
        ).fetchall()

        metadata = dict(
            rows
        )

        try:
            schema_version = int(
                metadata[
                    "schema_version"
                ]
            )

            expected_count = int(
                metadata[
                    "record_count"
                ]
            )

            source_mtime_epoch_s = float(
                metadata[
                    "source_mtime_epoch_s"
                ]
            )

            now_epoch_s = float(
                self._now_provider()
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return False

        if (
            schema_version
            != SCHEMA_VERSION
            or expected_count < 0
            or not isfinite(
                source_mtime_epoch_s
            )
            or not isfinite(
                now_epoch_s
            )
        ):
            return False

        count_row = connection.execute(
            """
            SELECT COUNT(*)
            FROM obstacles
            """
        ).fetchone()

        if (
            count_row is None
            or count_row[0]
            != expected_count
        ):
            return False

        age_seconds = (
            now_epoch_s
            - source_mtime_epoch_s
        )

        # Reject a source timestamp more than one
        # day in the future as well as an old source.
        if age_seconds < -86400.0:
            return False

        maximum_age_seconds = (
            self.max_age_days
            * 86400.0
        )

        if (
            age_seconds
            > maximum_age_seconds
        ):
            return False

        return True

    @staticmethod
    def _query_rows(
        connection: sqlite3.Connection,
        *,
        minimum_latitude: float,
        maximum_latitude: float,
        minimum_longitude: float,
        maximum_longitude: float,
        longitude_delta_deg: float,
    ) -> list[
        tuple[
            str,
            float,
            float,
            float,
            float,
        ]
    ]:
        select_columns = """
            SELECT
                ident,
                lat_deg,
                lon_deg,
                elevation_ft,
                height_agl_ft
            FROM obstacles
        """

        if longitude_delta_deg >= 180.0:
            return connection.execute(
                select_columns
                + """
                WHERE lat_deg
                    BETWEEN ? AND ?
                """,
                (
                    minimum_latitude,
                    maximum_latitude,
                ),
            ).fetchall()

        if minimum_longitude < -180.0:
            wrapped_minimum = (
                minimum_longitude
                + 360.0
            )

            return connection.execute(
                select_columns
                + """
                WHERE lat_deg
                    BETWEEN ? AND ?
                  AND (
                    lon_deg >= ?
                    OR lon_deg <= ?
                  )
                """,
                (
                    minimum_latitude,
                    maximum_latitude,
                    wrapped_minimum,
                    maximum_longitude,
                ),
            ).fetchall()

        if maximum_longitude > 180.0:
            wrapped_maximum = (
                maximum_longitude
                - 360.0
            )

            return connection.execute(
                select_columns
                + """
                WHERE lat_deg
                    BETWEEN ? AND ?
                  AND (
                    lon_deg >= ?
                    OR lon_deg <= ?
                  )
                """,
                (
                    minimum_latitude,
                    maximum_latitude,
                    minimum_longitude,
                    wrapped_maximum,
                ),
            ).fetchall()

        return connection.execute(
            select_columns
            + """
            WHERE lat_deg
                BETWEEN ? AND ?
              AND lon_deg
                BETWEEN ? AND ?
            """,
            (
                minimum_latitude,
                maximum_latitude,
                minimum_longitude,
                maximum_longitude,
            ),
        ).fetchall()

    @staticmethod
    def _query_valid(
        aircraft_lat_deg: float,
        aircraft_lon_deg: float,
        max_distance_nm: float,
    ) -> bool:
        return (
            all(
                isfinite(value)
                for value in (
                    aircraft_lat_deg,
                    aircraft_lon_deg,
                    max_distance_nm,
                )
            )
            and (
                -90.0
                <= aircraft_lat_deg
                <= 90.0
            )
            and (
                -180.0
                <= aircraft_lon_deg
                <= 180.0
            )
            and max_distance_nm > 0.0
        )
