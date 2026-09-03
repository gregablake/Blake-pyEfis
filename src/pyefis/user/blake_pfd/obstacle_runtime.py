from __future__ import annotations

from collections.abc import Callable
from math import (
    atan2,
    cos,
    isfinite,
    radians,
    sin,
    sqrt,
)
from time import monotonic

from pyefis.user.blake_pfd.obstacle_database import (
    ObstacleDatabase,
)
from pyefis.user.blake_pfd.obstacles import (
    EARTH_RADIUS_NM,
    ObstacleComputer,
    ObstacleState,
)


class ObstacleRuntimeProvider:
    def __init__(
        self,
        database: ObstacleDatabase,
        *,
        max_distance_nm: float = 10.0,
        refresh_distance_nm: float = 1.0,
        warning_distance_nm: float = 3.0,
        warning_clearance_ft: float = 1000.0,
        evaluation_interval_s: float = 0.10,
        evaluation_movement_nm: float = 0.05,
        evaluation_altitude_ft: float = 50.0,
        now_provider: Callable[
            [],
            float,
        ] = monotonic,
    ) -> None:
        self.database = database

        self.max_distance_nm = float(
            max_distance_nm
        )

        self.refresh_distance_nm = float(
            refresh_distance_nm
        )

        self.warning_distance_nm = float(
            warning_distance_nm
        )

        self.warning_clearance_ft = float(
            warning_clearance_ft
        )

        self.evaluation_interval_s = float(
            evaluation_interval_s
        )

        self.evaluation_movement_nm = float(
            evaluation_movement_nm
        )

        self.evaluation_altitude_ft = float(
            evaluation_altitude_ft
        )

        self._now_provider = now_provider

        self._query_center_lat_deg: (
            float | None
        ) = None

        self._query_center_lon_deg: (
            float | None
        ) = None

        self._computer: (
            ObstacleComputer | None
        ) = None

        self._state: (
            ObstacleState | None
        ) = None

        self._last_evaluation_s: (
            float | None
        ) = None

        self._last_evaluation_lat_deg: (
            float | None
        ) = None

        self._last_evaluation_lon_deg: (
            float | None
        ) = None

        self._last_evaluation_alt_ft: (
            float | None
        ) = None

    def update(
        self,
        *,
        aircraft_lat: float,
        aircraft_lon: float,
        aircraft_alt_ft: float,
    ) -> ObstacleState:
        now_s = float(
            self._now_provider()
        )

        if (
            not self._inputs_valid(
                aircraft_lat,
                aircraft_lon,
                aircraft_alt_ft,
            )
            or not isfinite(now_s)
        ):
            self._state = None
            self._last_evaluation_s = None

            return self._unavailable()

        database_refreshed = False

        if self._needs_refresh(
            aircraft_lat,
            aircraft_lon,
        ):
            query_radius_nm = (
                self.max_distance_nm
                + self.refresh_distance_nm
            )

            candidates = (
                self.database
                .query_candidates(
                    aircraft_lat_deg=(
                        aircraft_lat
                    ),
                    aircraft_lon_deg=(
                        aircraft_lon
                    ),
                    max_distance_nm=(
                        query_radius_nm
                    ),
                )
            )

            if candidates is None:
                # Never continue displaying stale
                # obstacle data after a database
                # query failure.
                self._computer = None
                self._query_center_lat_deg = None
                self._query_center_lon_deg = None
                self._state = None
                self._last_evaluation_s = None

                return self._unavailable()

            self._computer = (
                ObstacleComputer(
                    candidates,
                    max_distance_nm=(
                        self.max_distance_nm
                    ),
                    warning_distance_nm=(
                        self.warning_distance_nm
                    ),
                    warning_clearance_ft=(
                        self.warning_clearance_ft
                    ),
                )
            )

            self._query_center_lat_deg = (
                aircraft_lat
            )

            self._query_center_lon_deg = (
                aircraft_lon
            )

            database_refreshed = True

        if self._computer is None:
            return self._unavailable()

        if (
            database_refreshed
            or self._needs_evaluation(
                now_s=now_s,
                aircraft_lat=aircraft_lat,
                aircraft_lon=aircraft_lon,
                aircraft_alt_ft=(
                    aircraft_alt_ft
                ),
            )
        ):
            self._state = (
                self._computer.update(
                    aircraft_lat=aircraft_lat,
                    aircraft_lon=aircraft_lon,
                    aircraft_alt_ft=(
                        aircraft_alt_ft
                    ),
                )
            )

            self._last_evaluation_s = now_s

            self._last_evaluation_lat_deg = (
                aircraft_lat
            )

            self._last_evaluation_lon_deg = (
                aircraft_lon
            )

            self._last_evaluation_alt_ft = (
                aircraft_alt_ft
            )

        if self._state is None:
            return self._unavailable()

        return self._state

    def _needs_refresh(
        self,
        aircraft_lat: float,
        aircraft_lon: float,
    ) -> bool:
        if (
            self._computer is None
            or self._query_center_lat_deg
            is None
            or self._query_center_lon_deg
            is None
        ):
            return True

        movement_nm = self._distance_nm(
            self._query_center_lat_deg,
            self._query_center_lon_deg,
            aircraft_lat,
            aircraft_lon,
        )

        return (
            not isfinite(movement_nm)
            or movement_nm
            >= self.refresh_distance_nm
        )

    def _needs_evaluation(
        self,
        *,
        now_s: float,
        aircraft_lat: float,
        aircraft_lon: float,
        aircraft_alt_ft: float,
    ) -> bool:
        if (
            self._state is None
            or self._last_evaluation_s
            is None
            or self._last_evaluation_lat_deg
            is None
            or self._last_evaluation_lon_deg
            is None
            or self._last_evaluation_alt_ft
            is None
        ):
            return True

        elapsed_s = (
            now_s
            - self._last_evaluation_s
        )

        if (
            not isfinite(elapsed_s)
            or elapsed_s < 0.0
            or elapsed_s
            >= self.evaluation_interval_s
        ):
            return True

        movement_nm = self._distance_nm(
            self._last_evaluation_lat_deg,
            self._last_evaluation_lon_deg,
            aircraft_lat,
            aircraft_lon,
        )

        if (
            not isfinite(movement_nm)
            or movement_nm
            >= self.evaluation_movement_nm
        ):
            return True

        altitude_change_ft = abs(
            aircraft_alt_ft
            - self._last_evaluation_alt_ft
        )

        return (
            altitude_change_ft
            >= self.evaluation_altitude_ft
        )

    def _inputs_valid(
        self,
        aircraft_lat: float,
        aircraft_lon: float,
        aircraft_alt_ft: float,
    ) -> bool:
        settings = (
            self.max_distance_nm,
            self.refresh_distance_nm,
            self.warning_distance_nm,
            self.warning_clearance_ft,
            self.evaluation_interval_s,
            self.evaluation_movement_nm,
            self.evaluation_altitude_ft,
        )

        return (
            all(
                isfinite(value)
                for value in (
                    aircraft_lat,
                    aircraft_lon,
                    aircraft_alt_ft,
                    *settings,
                )
            )
            and -90.0
            <= aircraft_lat
            <= 90.0
            and -180.0
            <= aircraft_lon
            <= 180.0
            and self.max_distance_nm > 0.0
            and self.refresh_distance_nm
            > 0.0
            and self.warning_distance_nm
            > 0.0
            and self.warning_clearance_ft
            >= 0.0
            and self.evaluation_interval_s
            > 0.0
            and self.evaluation_movement_nm
            > 0.0
            and self.evaluation_altitude_ft
            > 0.0
        )

    @staticmethod
    def _distance_nm(
        lat1_deg: float,
        lon1_deg: float,
        lat2_deg: float,
        lon2_deg: float,
    ) -> float:
        lat1 = radians(lat1_deg)
        lon1 = radians(lon1_deg)
        lat2 = radians(lat2_deg)
        lon2 = radians(lon2_deg)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            sin(
                delta_lat / 2.0
            ) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(
                delta_lon / 2.0
            ) ** 2
        )

        c = 2.0 * atan2(
            sqrt(a),
            sqrt(
                max(
                    0.0,
                    1.0 - a,
                )
            ),
        )

        return (
            EARTH_RADIUS_NM
            * c
        )

    @staticmethod
    def _unavailable() -> ObstacleState:
        return ObstacleState(
            ok=False,
            nearby=[],
            warning=False,
        )
