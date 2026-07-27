from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from pyefis.user.blake_pfd.core.glide_calculator import (
    FEET_PER_NAUTICAL_MILE,
    GlideCalculation,
)


@dataclass(frozen=True)
class AirportGlideCandidate:
    identifier: str = ""
    distance_nm: float = 0.0
    bearing_deg: float = 0.0
    airport_elevation_ft: float = 0.0
    required_glide_ratio: float = 0.0
    arrival_altitude_ft: float = 0.0
    safety_margin_ft: float = 0.0
    reachable: bool = False
    valid: bool = False


class AirportGlideAnalyzer:
    def analyze(
        self,
        identifier: str,
        distance_nm,
        bearing_deg,
        airport_elevation_ft,
        aircraft_altitude_ft,
        glide: GlideCalculation,
    ) -> AirportGlideCandidate:
        distance = self._safe_nonnegative(
            distance_nm
        )

        bearing = self._safe_angle(
            bearing_deg
        )

        airport_elevation = self._safe_nonnegative(
            airport_elevation_ft
        )

        aircraft_altitude = self._safe_nonnegative(
            aircraft_altitude_ft
        )

        if (
            distance is None
            or bearing is None
            or airport_elevation is None
            or aircraft_altitude is None
            or glide is None
            or not glide.valid
        ):
            return AirportGlideCandidate(
                identifier=str(identifier),
            )

        if distance <= 0.0:
            arrival_altitude_ft = aircraft_altitude

            safety_margin_ft = (
                arrival_altitude_ft
                - airport_elevation
            )

            return AirportGlideCandidate(
                identifier=str(identifier),
                distance_nm=0.0,
                bearing_deg=bearing,
                airport_elevation_ft=airport_elevation,
                required_glide_ratio=0.0,
                arrival_altitude_ft=arrival_altitude_ft,
                safety_margin_ft=safety_margin_ft,
                reachable=True,
                valid=True,
            )

        if glide.altitude_available_ft <= 0.0:
            return AirportGlideCandidate(
                identifier=str(identifier),
                distance_nm=distance,
                bearing_deg=bearing,
                airport_elevation_ft=airport_elevation,
                valid=True,
            )

        required_altitude_loss_ft = (
            distance
            * FEET_PER_NAUTICAL_MILE
        )

        effective_glide_ratio = (
            glide.wind_corrected_range_nm
            * FEET_PER_NAUTICAL_MILE
            / glide.altitude_available_ft
        )

        if effective_glide_ratio <= 0.0:
            return AirportGlideCandidate(
                identifier=str(identifier),
                distance_nm=distance,
                bearing_deg=bearing,
                airport_elevation_ft=airport_elevation,
                valid=True,
            )

        altitude_loss_ft = (
            required_altitude_loss_ft
            / effective_glide_ratio
        )

        arrival_altitude_ft = (
            aircraft_altitude
            - altitude_loss_ft
        )

        safety_margin_ft = (
            arrival_altitude_ft
            - airport_elevation
        )

        required_glide_ratio = (
            required_altitude_loss_ft
            / max(
                1.0,
                aircraft_altitude
                - airport_elevation,
            )
        )

        reachable = (
            distance
            <= glide.wind_corrected_range_nm
            and safety_margin_ft >= 0.0
        )

        return AirportGlideCandidate(
            identifier=str(identifier),
            distance_nm=distance,
            bearing_deg=bearing,
            airport_elevation_ft=airport_elevation,
            required_glide_ratio=required_glide_ratio,
            arrival_altitude_ft=arrival_altitude_ft,
            safety_margin_ft=safety_margin_ft,
            reachable=reachable,
            valid=True,
        )

    @staticmethod
    def _safe_nonnegative(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return max(
            0.0,
            number,
        )

    @staticmethod
    def _safe_angle(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return number % 360.0