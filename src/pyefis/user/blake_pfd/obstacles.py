from __future__ import annotations

from dataclasses import dataclass
from math import (
    atan2,
    cos,
    isfinite,
    radians,
    sin,
    sqrt,
)


EARTH_RADIUS_NM = 3440.065


@dataclass(frozen=True)
class Obstacle:
    ident: str
    lat_deg: float
    lon_deg: float
    elevation_ft: float
    height_agl_ft: float
    distance_nm: float = 0.0
    bearing_deg: float = 0.0


@dataclass
class ObstacleState:
    ok: bool = True
    nearby: list[Obstacle] | None = None
    warning: bool = False


class ObstacleComputer:
    def __init__(
        self,
        obstacles: list[Obstacle] | tuple[Obstacle, ...] | None = None,
        *,
        max_distance_nm: float = 10.0,
        warning_distance_nm: float = 3.0,
        warning_clearance_ft: float = 1000.0,
    ) -> None:
        # None means no obstacle database has been loaded.
        # An empty sequence means a valid database containing
        # no obstacle records.
        self._source_available = (
            obstacles is not None
        )

        self._obstacles = tuple(
            obstacles or ()
        )

        self.max_distance_nm = float(
            max_distance_nm
        )

        self.warning_distance_nm = float(
            warning_distance_nm
        )

        self.warning_clearance_ft = float(
            warning_clearance_ft
        )

    def update(
        self,
        aircraft_lat: float,
        aircraft_lon: float,
        aircraft_alt_ft: float,
    ) -> ObstacleState:
        if not self._source_available:
            return ObstacleState(
                ok=False,
                nearby=[],
                warning=False,
            )

        if not self._aircraft_position_valid(
            aircraft_lat,
            aircraft_lon,
            aircraft_alt_ft,
        ):
            return ObstacleState(
                ok=False,
                nearby=[],
                warning=False,
            )

        if not self._settings_valid():
            return ObstacleState(
                ok=False,
                nearby=[],
                warning=False,
            )

        nearby_with_threat: list[
            tuple[
                bool,
                Obstacle,
            ]
        ] = []

        for obstacle in self._obstacles:
            if not self._obstacle_valid(
                obstacle
            ):
                continue

            distance_nm = (
                self._distance_nm(
                    aircraft_lat,
                    aircraft_lon,
                    obstacle.lat_deg,
                    obstacle.lon_deg,
                )
            )

            bearing_deg = (
                self._bearing_deg(
                    aircraft_lat,
                    aircraft_lon,
                    obstacle.lat_deg,
                    obstacle.lon_deg,
                )
            )

            if (
                not isfinite(distance_nm)
                or not isfinite(bearing_deg)
            ):
                continue

            if (
                distance_nm
                > self.max_distance_nm
            ):
                continue

            computed = Obstacle(
                ident=obstacle.ident,
                lat_deg=obstacle.lat_deg,
                lon_deg=obstacle.lon_deg,
                elevation_ft=(
                    obstacle.elevation_ft
                ),
                height_agl_ft=(
                    obstacle.height_agl_ft
                ),
                distance_nm=distance_nm,
                bearing_deg=bearing_deg,
            )

            vertical_clearance_ft = (
                aircraft_alt_ft
                - obstacle.elevation_ft
            )

            threat = (
                distance_nm
                < self.warning_distance_nm
                and vertical_clearance_ft
                < self.warning_clearance_ft
            )

            nearby_with_threat.append(
                (
                    threat,
                    computed,
                )
            )

        # Any warning obstacle is presented first so the
        # renderer cannot show a safe obstacle in a red box
        # while a different obstacle caused the warning.
        nearby_with_threat.sort(
            key=lambda item: (
                not item[0],
                item[1].distance_nm,
            )
        )

        nearby = [
            obstacle
            for _, obstacle
            in nearby_with_threat
        ]

        warning = any(
            threat
            for threat, _
            in nearby_with_threat
        )

        return ObstacleState(
            ok=True,
            nearby=nearby,
            warning=warning,
        )

    def _settings_valid(self) -> bool:
        values = (
            self.max_distance_nm,
            self.warning_distance_nm,
            self.warning_clearance_ft,
        )

        return (
            all(
                isfinite(value)
                for value in values
            )
            and self.max_distance_nm > 0.0
            and self.warning_distance_nm
            > 0.0
            and self.warning_clearance_ft
            >= 0.0
        )

    @staticmethod
    def _aircraft_position_valid(
        lat_deg: float,
        lon_deg: float,
        altitude_ft: float,
    ) -> bool:
        return (
            all(
                isfinite(value)
                for value in (
                    lat_deg,
                    lon_deg,
                    altitude_ft,
                )
            )
            and -90.0 <= lat_deg <= 90.0
            and -180.0 <= lon_deg <= 180.0
        )

    @staticmethod
    def _obstacle_valid(
        obstacle: Obstacle,
    ) -> bool:
        return (
            isinstance(
                obstacle.ident,
                str,
            )
            and bool(
                obstacle.ident.strip()
            )
            and all(
                isfinite(value)
                for value in (
                    obstacle.lat_deg,
                    obstacle.lon_deg,
                    obstacle.elevation_ft,
                    obstacle.height_agl_ft,
                )
            )
            and (
                -90.0
                <= obstacle.lat_deg
                <= 90.0
            )
            and (
                -180.0
                <= obstacle.lon_deg
                <= 180.0
            )
            and obstacle.height_agl_ft
            >= 0.0
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
            sin(delta_lat / 2.0) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2.0) ** 2
        )

        c = 2.0 * atan2(
            sqrt(a),
            sqrt(max(0.0, 1.0 - a)),
        )

        return EARTH_RADIUS_NM * c

    @staticmethod
    def _bearing_deg(
        lat1_deg: float,
        lon1_deg: float,
        lat2_deg: float,
        lon2_deg: float,
    ) -> float:
        lat1 = radians(lat1_deg)
        lat2 = radians(lat2_deg)
        delta_lon = radians(
            lon2_deg - lon1_deg
        )

        y = (
            sin(delta_lon)
            * cos(lat2)
        )

        x = (
            cos(lat1)
            * sin(lat2)
            - sin(lat1)
            * cos(lat2)
            * cos(delta_lon)
        )

        bearing = (
            atan2(y, x)
            * 180.0
            / 3.141592653589793
        )

        return (
            bearing + 360.0
        ) % 360.0
