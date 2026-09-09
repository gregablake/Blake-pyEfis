from __future__ import annotations

import os
from email.utils import parsedate_to_datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time_ns
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

from pyefis.user.blake_pfd.obstacle_database import (
    ObstacleDatabaseBuilder,
)


DAILY_DOF_URL = (
    "https://aeronav.faa.gov/"
    "Obst_Data/DAILY_DOF_CSV.ZIP"
)


class FaaObstacleUpdateError(RuntimeError):
    pass


class FaaObstacleUpdater:
    def __init__(
        self,
        *,
        opener=urlopen,
        builder: ObstacleDatabaseBuilder | None = None,
    ) -> None:
        self._opener = opener
        self._builder = (
            builder
            if builder is not None
            else ObstacleDatabaseBuilder()
        )

    def update(
        self,
        database_path: str | Path,
    ) -> int:
        try:
            payload, source_epoch_s = (
                self._download_current_archive()
            )

            csv_bytes = (
                self._read_dof_csv(
                    payload
                )
            )

            with TemporaryDirectory(
                prefix="blake_faa_dof_"
            ) as temp_directory:
                source_path = (
                    Path(temp_directory)
                    / "DOF.CSV"
                )

                source_path.write_bytes(
                    csv_bytes
                )

                # Preserve the FAA server's
                # Last-Modified timestamp so the
                # existing schema-v1 builder stores
                # upstream provenance rather than
                # local download time.
                os.utime(
                    source_path,
                    (
                        source_epoch_s,
                        source_epoch_s,
                    ),
                )

                return self._builder.build(
                    source_path,
                    database_path,
                )

        except FaaObstacleUpdateError:
            raise

        except Exception as exc:
            raise FaaObstacleUpdateError(
                "FAA obstacle update failed"
            ) from exc

    def _download_current_archive(
        self,
    ) -> tuple[bytes, float]:
        cache_buster = str(
            time_ns()
        )

        separator = (
            "&"
            if "?" in DAILY_DOF_URL
            else "?"
        )

        url = (
            DAILY_DOF_URL
            + separator
            + urlencode(
                {
                    "cb": cache_buster,
                }
            )
        )

        request = Request(
            url,
            headers={
                "Cache-Control": "no-cache",
                "User-Agent": (
                    "Blake-pyEfis/"
                    "FAA-obstacle-updater"
                ),
            },
            method="GET",
        )

        try:
            with self._opener(
                request
            ) as response:
                payload = response.read()

                last_modified = (
                    response.headers.get(
                        "Last-Modified"
                    )
                )

        except Exception as exc:
            raise FaaObstacleUpdateError(
                "Unable to download FAA "
                "Daily DOF archive"
            ) from exc

        if not payload:
            raise FaaObstacleUpdateError(
                "FAA Daily DOF archive "
                "was empty"
            )

        if not last_modified:
            raise FaaObstacleUpdateError(
                "FAA Daily DOF response "
                "did not include "
                "Last-Modified"
            )

        try:
            modified_datetime = (
                parsedate_to_datetime(
                    last_modified
                )
            )

            if (
                modified_datetime
                .tzinfo
                is None
            ):
                raise ValueError(
                    "timezone missing"
                )

            source_epoch_s = (
                modified_datetime
                .timestamp()
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as exc:
            raise FaaObstacleUpdateError(
                "FAA Daily DOF "
                "Last-Modified was invalid"
            ) from exc

        return (
            payload,
            source_epoch_s,
        )

    @staticmethod
    def _read_dof_csv(
        payload: bytes,
    ) -> bytes:
        try:
            with ZipFile(
                BytesIO(payload)
            ) as archive:
                matches = [
                    name
                    for name
                    in archive.namelist()
                    if (
                        not name.endswith("/")
                        and Path(
                            name
                        ).name.upper()
                        == "DOF.CSV"
                    )
                ]

                if len(matches) != 1:
                    raise FaaObstacleUpdateError(
                        "FAA Daily DOF archive "
                        "must contain exactly "
                        "one DOF.CSV"
                    )

                csv_bytes = (
                    archive.read(
                        matches[0]
                    )
                )

        except FaaObstacleUpdateError:
            raise

        except (
            BadZipFile,
            KeyError,
            OSError,
        ) as exc:
            raise FaaObstacleUpdateError(
                "FAA Daily DOF archive "
                "was invalid"
            ) from exc

        if not csv_bytes:
            raise FaaObstacleUpdateError(
                "FAA DOF.CSV was empty"
            )

        return csv_bytes
