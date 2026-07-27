from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


FEET_PER_NAUTICAL_MILE = 6076.12


@dataclass(frozen=True)
class GlideCalculation:
    altitude_available_ft: float = 0.0
    still_air_range_nm: float = 0.0
    wind_corrected_range_nm: float = 0.0
    glide_time_min: float = 0.0
    ground_speed_kt: float = 0.0
    valid: bool = False


class GlideCalculator:
    def __init__(
        self,
        glide_ratio: float = 9.0,
        best_glide_speed_kt: float = 80.0,
        reserve_altitude_ft: float = 1000.0,
        minimum_ground_speed_kt: float = 20.0,
    ) -> None:
        self.glide_ratio = self._require_positive(
            glide_ratio,
            "glide_ratio",
        )

        self.best_glide_speed_kt = self._require_positive(
            best_glide_speed_kt,
            "best_glide_speed_kt",
        )

        self.reserve_altitude_ft = self._require_nonnegative(
            reserve_altitude_ft,
            "reserve_altitude_ft",
        )

        self.minimum_ground_speed_kt = self._require_positive(
            minimum_ground_speed_kt,
            "minimum_ground_speed_kt",
        )

    def calculate(
        self,
        altitude_ft,
        terrain_elevation_ft=0.0,
        headwind_kt=0.0,
        tailwind_kt=0.0,
    ) -> GlideCalculation:
        altitude = self._safe_nonnegative(
            altitude_ft
        )

        terrain_elevation = self._safe_nonnegative(
            terrain_elevation_ft
        )

        headwind = self._safe_nonnegative(
            headwind_kt
        )

        tailwind = self._safe_nonnegative(
            tailwind_kt
        )

        if (
            altitude is None
            or terrain_elevation is None
            or headwind is None
            or tailwind is None
        ):
            return GlideCalculation()

        altitude_available_ft = max(
            0.0,
            altitude
            - terrain_elevation
            - self.reserve_altitude_ft,
        )

        if altitude_available_ft <= 0.0:
            return GlideCalculation(
                altitude_available_ft=0.0,
                valid=True,
            )

        still_air_range_nm = (
            altitude_available_ft
            * self.glide_ratio
            / FEET_PER_NAUTICAL_MILE
        )

        sink_rate_fpm = (
            self.best_glide_speed_kt
            * FEET_PER_NAUTICAL_MILE
            / 60.0
            / self.glide_ratio
        )

        glide_time_min = (
            altitude_available_ft
            / sink_rate_fpm
        )

        ground_speed_kt = (
            self.best_glide_speed_kt
            - headwind
            + tailwind
        )

        ground_speed_kt = max(
            self.minimum_ground_speed_kt,
            ground_speed_kt,
        )

        wind_corrected_range_nm = (
            ground_speed_kt
            * glide_time_min
            / 60.0
        )

        return GlideCalculation(
            altitude_available_ft=(
                altitude_available_ft
            ),
            still_air_range_nm=(
                still_air_range_nm
            ),
            wind_corrected_range_nm=(
                wind_corrected_range_nm
            ),
            glide_time_min=glide_time_min,
            ground_speed_kt=ground_speed_kt,
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
    def _require_positive(
        value,
        name: str,
    ) -> float:
        number = float(value)

        if not isfinite(number) or number <= 0.0:
            raise ValueError(
                f"{name} must be finite and positive"
            )

        return number

    @staticmethod
    def _require_nonnegative(
        value,
        name: str,
    ) -> float:
        number = float(value)

        if not isfinite(number) or number < 0.0:
            raise ValueError(
                f"{name} must be finite and not negative"
            )

        return number