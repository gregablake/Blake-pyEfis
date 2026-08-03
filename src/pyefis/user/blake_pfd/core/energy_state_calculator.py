from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


KNOT_TO_FEET_PER_SECOND = 1.68781
GRAVITY_FT_PER_SECOND_SQUARED = 32.174


@dataclass(frozen=True)
class EnergyState:
    altitude_above_terrain_ft: float = 0.0
    potential_energy_height_ft: float = 0.0
    kinetic_energy_height_ft: float = 0.0
    total_energy_height_ft: float = 0.0
    energy_trend_fpm: float = 0.0
    glide_margin_nm: float | None = None
    climb_margin_ft: float | None = None
    trend: str = "STABLE"
    valid: bool = False


class EnergyStateCalculator:
    def __init__(
        self,
        stable_trend_threshold_fpm: float = 50.0,
    ) -> None:
        self.stable_trend_threshold_fpm = (
            self._require_nonnegative(
                stable_trend_threshold_fpm,
                "stable_trend_threshold_fpm",
            )
        )

        self._previous_total_energy_height_ft: (
            float | None
        ) = None
        self._previous_timestamp_s: float | None = None

    def reset(self) -> None:
        self._previous_total_energy_height_ft = None
        self._previous_timestamp_s = None

    def calculate(
        self,
        *,
        altitude_ft,
        terrain_elevation_ft=0.0,
        airspeed_kt=0.0,
        timestamp_s=None,
        selected_site_distance_nm=None,
        glide_range_nm=None,
        target_altitude_ft=None,
    ) -> EnergyState:
        altitude = self._safe_number(
            altitude_ft
        )
        terrain_elevation = self._safe_number(
            terrain_elevation_ft
        )
        airspeed = self._safe_nonnegative(
            airspeed_kt
        )

        if (
            altitude is None
            or terrain_elevation is None
            or airspeed is None
        ):
            return EnergyState()

        altitude_above_terrain_ft = max(
            0.0,
            altitude - terrain_elevation,
        )

        potential_energy_height_ft = (
            altitude_above_terrain_ft
        )

        airspeed_fps = (
            airspeed
            * KNOT_TO_FEET_PER_SECOND
        )

        kinetic_energy_height_ft = (
            airspeed_fps**2
            / (
                2.0
                * GRAVITY_FT_PER_SECOND_SQUARED
            )
        )

        total_energy_height_ft = (
            potential_energy_height_ft
            + kinetic_energy_height_ft
        )

        energy_trend_fpm = self._calculate_trend(
            total_energy_height_ft=(
                total_energy_height_ft
            ),
            timestamp_s=timestamp_s,
        )

        trend = self._classify_trend(
            energy_trend_fpm
        )

        glide_margin_nm = self._calculate_glide_margin(
            selected_site_distance_nm=(
                selected_site_distance_nm
            ),
            glide_range_nm=glide_range_nm,
        )

        climb_margin_ft = self._calculate_climb_margin(
            altitude_ft=altitude,
            target_altitude_ft=target_altitude_ft,
        )

        return EnergyState(
            altitude_above_terrain_ft=(
                altitude_above_terrain_ft
            ),
            potential_energy_height_ft=(
                potential_energy_height_ft
            ),
            kinetic_energy_height_ft=(
                kinetic_energy_height_ft
            ),
            total_energy_height_ft=(
                total_energy_height_ft
            ),
            energy_trend_fpm=energy_trend_fpm,
            glide_margin_nm=glide_margin_nm,
            climb_margin_ft=climb_margin_ft,
            trend=trend,
            valid=True,
        )

    def _calculate_trend(
        self,
        *,
        total_energy_height_ft: float,
        timestamp_s,
    ) -> float:
        timestamp = self._safe_number(
            timestamp_s
        )

        if timestamp is None:
            return 0.0

        previous_energy = (
            self._previous_total_energy_height_ft
        )
        previous_timestamp = (
            self._previous_timestamp_s
        )

        self._previous_total_energy_height_ft = (
            total_energy_height_ft
        )
        self._previous_timestamp_s = timestamp

        if (
            previous_energy is None
            or previous_timestamp is None
        ):
            return 0.0

        elapsed_s = timestamp - previous_timestamp

        if elapsed_s <= 0.0:
            return 0.0

        energy_change_ft = (
            total_energy_height_ft
            - previous_energy
        )

        return (
            energy_change_ft
            / elapsed_s
            * 60.0
        )

    def _classify_trend(
        self,
        energy_trend_fpm: float,
    ) -> str:
        threshold = (
            self.stable_trend_threshold_fpm
        )

        if energy_trend_fpm > threshold:
            return "INCREASING"

        if energy_trend_fpm < -threshold:
            return "DECREASING"

        return "STABLE"

    @staticmethod
    def _calculate_glide_margin(
        *,
        selected_site_distance_nm,
        glide_range_nm,
    ) -> float | None:
        distance = EnergyStateCalculator._safe_nonnegative(
            selected_site_distance_nm
        )
        glide_range = EnergyStateCalculator._safe_nonnegative(
            glide_range_nm
        )

        if distance is None or glide_range is None:
            return None

        return glide_range - distance

    @staticmethod
    def _calculate_climb_margin(
        *,
        altitude_ft: float,
        target_altitude_ft,
    ) -> float | None:
        target_altitude = (
            EnergyStateCalculator._safe_number(
                target_altitude_ft
            )
        )

        if target_altitude is None:
            return None

        return altitude_ft - target_altitude

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
        number = EnergyStateCalculator._safe_number(
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