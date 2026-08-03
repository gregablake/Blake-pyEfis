from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TerrainProfilePoint:
    distance_nm: float
    elevation_ft: float


@dataclass(frozen=True)
class TerrainAwarenessState:
    highest_terrain_ft: float = 0.0
    minimum_clearance_ft: float = 0.0
    limiting_distance_nm: float | None = None
    projected_altitude_ft: float = 0.0
    warning_level: str = "NONE"
    message: str = ""
    valid: bool = False


class TerrainAwareness:
    def __init__(
        self,
        *,
        caution_clearance_ft: float = 1000.0,
        warning_clearance_ft: float = 500.0,
        critical_clearance_ft: float = 100.0,
    ) -> None:
        self.caution_clearance_ft = self._require_nonnegative(
            caution_clearance_ft,
            "caution_clearance_ft",
        )
        self.warning_clearance_ft = self._require_nonnegative(
            warning_clearance_ft,
            "warning_clearance_ft",
        )
        self.critical_clearance_ft = self._require_nonnegative(
            critical_clearance_ft,
            "critical_clearance_ft",
        )

        if not (
            self.caution_clearance_ft
            >= self.warning_clearance_ft
            >= self.critical_clearance_ft
        ):
            raise ValueError(
                "clearance thresholds must satisfy "
                "caution >= warning >= critical"
            )

    def evaluate(
        self,
        *,
        aircraft_altitude_ft,
        vertical_speed_fpm=0.0,
        ground_speed_kt=0.0,
        profile: list[TerrainProfilePoint] | tuple[
            TerrainProfilePoint,
            ...,
        ] = (),
    ) -> TerrainAwarenessState:
        altitude = self._safe_number(
            aircraft_altitude_ft
        )
        vertical_speed = self._safe_number(
            vertical_speed_fpm
        )
        ground_speed = self._safe_nonnegative(
            ground_speed_kt
        )

        if (
            altitude is None
            or vertical_speed is None
            or ground_speed is None
        ):
            return TerrainAwarenessState()

        if not profile:
            return TerrainAwarenessState(
                projected_altitude_ft=altitude,
                message="TERRAIN DATA UNAVAILABLE",
                valid=False,
            )

        normalized_profile: list[
            TerrainProfilePoint
        ] = []

        for point in profile:
            distance = self._safe_nonnegative(
                point.distance_nm
            )
            elevation = self._safe_number(
                point.elevation_ft
            )

            if distance is None or elevation is None:
                return TerrainAwarenessState(
                    projected_altitude_ft=altitude,
                    message="TERRAIN DATA INVALID",
                    valid=False,
                )

            normalized_profile.append(
                TerrainProfilePoint(
                    distance_nm=distance,
                    elevation_ft=elevation,
                )
            )

        minimum_clearance_ft: float | None = None
        limiting_distance_nm: float | None = None
        limiting_projected_altitude_ft = altitude
        highest_terrain_ft = max(
            point.elevation_ft
            for point in normalized_profile
        )

        for point in normalized_profile:
            projected_altitude_ft = (
                self._project_altitude(
                    aircraft_altitude_ft=altitude,
                    vertical_speed_fpm=vertical_speed,
                    ground_speed_kt=ground_speed,
                    distance_nm=point.distance_nm,
                )
            )

            clearance_ft = (
                projected_altitude_ft
                - point.elevation_ft
            )

            if (
                minimum_clearance_ft is None
                or clearance_ft
                < minimum_clearance_ft
            ):
                minimum_clearance_ft = clearance_ft
                limiting_distance_nm = (
                    point.distance_nm
                )
                limiting_projected_altitude_ft = (
                    projected_altitude_ft
                )

        assert minimum_clearance_ft is not None

        warning_level, message = (
            self._classify_clearance(
                minimum_clearance_ft
            )
        )

        return TerrainAwarenessState(
            highest_terrain_ft=highest_terrain_ft,
            minimum_clearance_ft=(
                minimum_clearance_ft
            ),
            limiting_distance_nm=(
                limiting_distance_nm
            ),
            projected_altitude_ft=(
                limiting_projected_altitude_ft
            ),
            warning_level=warning_level,
            message=message,
            valid=True,
        )

    @staticmethod
    def _project_altitude(
        *,
        aircraft_altitude_ft: float,
        vertical_speed_fpm: float,
        ground_speed_kt: float,
        distance_nm: float,
    ) -> float:
        if ground_speed_kt <= 0.0:
            return aircraft_altitude_ft

        time_minutes = (
            distance_nm
            / ground_speed_kt
            * 60.0
        )

        return (
            aircraft_altitude_ft
            + vertical_speed_fpm
            * time_minutes
        )

    def _classify_clearance(
        self,
        clearance_ft: float,
    ) -> tuple[str, str]:
        if clearance_ft <= self.critical_clearance_ft:
            return (
                "CRITICAL",
                "PULL UP",
            )

        if clearance_ft <= self.warning_clearance_ft:
            return (
                "WARNING",
                "TERRAIN AHEAD",
            )

        if clearance_ft <= self.caution_clearance_ft:
            return (
                "CAUTION",
                "TERRAIN CLEARANCE LOW",
            )

        return (
            "NONE",
            "",
        )

    @staticmethod
    def _safe_number(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return number

    @staticmethod
    def _safe_nonnegative(
        value,
    ) -> float | None:
        number = TerrainAwareness._safe_number(
            value
        )

        if number is None or number < 0.0:
            return None

        return number

    @staticmethod
    def _require_nonnegative(
        value,
        name: str,
    ) -> float:
        number = float(value)

        if not isfinite(number) or number < 0.0:
            raise ValueError(
                f"{name} must be finite and nonnegative"
            )

        return number