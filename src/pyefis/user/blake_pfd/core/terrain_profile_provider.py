from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import asin, atan2, cos, degrees, isfinite, radians, sin

from pyefis.user.blake_pfd.core.terrain_awareness import (
    TerrainProfilePoint,
)


EARTH_RADIUS_NM = 3440.065


@dataclass(frozen=True)
class TerrainProfile:
    points: tuple[TerrainProfilePoint, ...] = ()
    valid: bool = False
    message: str = ""


class TerrainProfileProvider:
    def __init__(
        self,
        *,
        elevation_sampler: Callable[
            [float, float],
            float | None,
        ],
        sample_distances_nm: tuple[float, ...] = (
            1.0,
            2.0,
            3.0,
            5.0,
            8.0,
            10.0,
        ),
    ) -> None:
        if not callable(elevation_sampler):
            raise TypeError(
                "elevation_sampler must be callable"
            )

        self.elevation_sampler = elevation_sampler
        self.sample_distances_nm = (
            self._validate_distances(
                sample_distances_nm
            )
        )

    def build_profile(
        self,
        *,
        aircraft_lat_deg,
        aircraft_lon_deg,
        course_deg,
    ) -> TerrainProfile:
        latitude = self._safe_latitude(
            aircraft_lat_deg
        )
        longitude = self._safe_longitude(
            aircraft_lon_deg
        )
        course = self._safe_angle(
            course_deg
        )

        if (
            latitude is None
            or longitude is None
            or course is None
        ):
            return TerrainProfile(
                message="AIRCRAFT POSITION INVALID",
            )

        points: list[TerrainProfilePoint] = []

        for distance_nm in self.sample_distances_nm:
            sample_latitude, sample_longitude = (
                self._destination_point(
                    latitude_deg=latitude,
                    longitude_deg=longitude,
                    bearing_deg=course,
                    distance_nm=distance_nm,
                )
            )

            elevation = self._safe_number(
                self.elevation_sampler(
                    sample_latitude,
                    sample_longitude,
                )
            )

            if elevation is None:
                return TerrainProfile(
                    points=tuple(points),
                    valid=False,
                    message="TERRAIN SAMPLE UNAVAILABLE",
                )

            points.append(
                TerrainProfilePoint(
                    distance_nm=distance_nm,
                    elevation_ft=elevation,
                )
            )

        return TerrainProfile(
            points=tuple(points),
            valid=True,
        )

    @staticmethod
    def _destination_point(
        *,
        latitude_deg: float,
        longitude_deg: float,
        bearing_deg: float,
        distance_nm: float,
    ) -> tuple[float, float]:
        latitude_rad = radians(
            latitude_deg
        )
        longitude_rad = radians(
            longitude_deg
        )
        bearing_rad = radians(
            bearing_deg
        )
        angular_distance = (
            distance_nm
            / EARTH_RADIUS_NM
        )

        destination_latitude_rad = asin(
            sin(latitude_rad)
            * cos(angular_distance)
            + cos(latitude_rad)
            * sin(angular_distance)
            * cos(bearing_rad)
        )

        destination_longitude_rad = (
            longitude_rad
            + atan2(
                sin(bearing_rad)
                * sin(angular_distance)
                * cos(latitude_rad),
                cos(angular_distance)
                - sin(latitude_rad)
                * sin(destination_latitude_rad),
            )
        )

        destination_latitude_deg = degrees(
            destination_latitude_rad
        )
        destination_longitude_deg = (
            (
                degrees(
                    destination_longitude_rad
                )
                + 540.0
            )
            % 360.0
            - 180.0
        )

        return (
            destination_latitude_deg,
            destination_longitude_deg,
        )

    @staticmethod
    def _validate_distances(
        distances,
    ) -> tuple[float, ...]:
        try:
            values = tuple(
                float(value)
                for value in distances
            )
        except (TypeError, ValueError):
            raise ValueError(
                "sample distances must be numeric"
            ) from None

        if not values:
            raise ValueError(
                "sample distances must not be empty"
            )

        previous_distance = 0.0

        for distance in values:
            if (
                not isfinite(distance)
                or distance <= 0.0
            ):
                raise ValueError(
                    "sample distances must be finite "
                    "and positive"
                )

            if distance <= previous_distance:
                raise ValueError(
                    "sample distances must be "
                    "strictly increasing"
                )

            previous_distance = distance

        return values

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
    def _safe_latitude(
        value,
    ) -> float | None:
        latitude = TerrainProfileProvider._safe_number(
            value
        )

        if (
            latitude is None
            or latitude < -90.0
            or latitude > 90.0
        ):
            return None

        return latitude

    @staticmethod
    def _safe_longitude(
        value,
    ) -> float | None:
        longitude = TerrainProfileProvider._safe_number(
            value
        )

        if (
            longitude is None
            or longitude < -180.0
            or longitude > 180.0
        ):
            return None

        return longitude

    @staticmethod
    def _safe_angle(
        value,
    ) -> float | None:
        angle = TerrainProfileProvider._safe_number(
            value
        )

        if angle is None:
            return None

        return angle % 360.0