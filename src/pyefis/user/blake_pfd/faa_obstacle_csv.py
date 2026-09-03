from __future__ import annotations

import csv
from collections.abc import Iterator
from math import isfinite
from pathlib import Path

from pyefis.user.blake_pfd.obstacles import (
    Obstacle,
)


class FaaObstacleCsvError(ValueError):
    pass


class FaaObstacleCsvLoader:
    REQUIRED_COLUMNS = frozenset(
        {
            "OAS",
            "VERIFIED STATUS",
            "LATDEC",
            "LONDEC",
            "AGL",
            "AMSL",
            "ACTION",
        }
    )

    VERIFIED_STATUSES = frozenset(
        {
            "O",
        }
    )

    def iter_obstacles(
        self,
        path: str | Path,
    ) -> Iterator[Obstacle]:
        csv_path = Path(path)

        with csv_path.open(
            "r",
            encoding="cp1252",
            newline="",
        ) as stream:
            reader = csv.DictReader(
                stream
            )

            fieldnames = set(
                reader.fieldnames
                or ()
            )

            missing = (
                self.REQUIRED_COLUMNS
                - fieldnames
            )

            if missing:
                missing_text = ", ".join(
                    sorted(missing)
                )

                raise FaaObstacleCsvError(
                    "FAA obstacle CSV missing "
                    f"required columns: "
                    f"{missing_text}"
                )

            for row in reader:
                obstacle = (
                    self._parse_row(row)
                )

                if obstacle is not None:
                    yield obstacle

    def _parse_row(
        self,
        row: dict[
            str,
            str | None,
        ],
    ) -> Obstacle | None:
        verified_status = (
            self._text(
                row.get(
                    "VERIFIED STATUS"
                )
            ).upper()
        )

        # Current FAA DDOF data uses O for
        # verified obstacles and U for
        # unverified obstacles.
        if (
            verified_status
            not in self.VERIFIED_STATUSES
        ):
            return None

        action = self._text(
            row.get("ACTION")
        ).upper()

        # D = dismantled.
        if action == "D":
            return None

        ident = self._text(
            row.get("OAS")
        )

        if not ident:
            return None

        lat_deg = self._float(
            row.get("LATDEC")
        )

        lon_deg = self._float(
            row.get("LONDEC")
        )

        height_agl_ft = self._float(
            row.get("AGL")
        )

        elevation_ft = self._float(
            row.get("AMSL")
        )

        if (
            lat_deg is None
            or lon_deg is None
            or height_agl_ft is None
            or elevation_ft is None
        ):
            return None

        if (
            not -90.0
            <= lat_deg
            <= 90.0
            or not -180.0
            <= lon_deg
            <= 180.0
            or height_agl_ft < 0.0
        ):
            return None

        return Obstacle(
            ident=ident,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            elevation_ft=elevation_ft,
            height_agl_ft=height_agl_ft,
        )

    @staticmethod
    def _text(
        value: str | None,
    ) -> str:
        return (
            value or ""
        ).strip()

    @staticmethod
    def _float(
        value: str | None,
    ) -> float | None:
        text = (
            value or ""
        ).strip()

        if not text:
            return None

        try:
            parsed = float(text)
        except (
            TypeError,
            ValueError,
        ):
            return None

        if not isfinite(parsed):
            return None

        return parsed
