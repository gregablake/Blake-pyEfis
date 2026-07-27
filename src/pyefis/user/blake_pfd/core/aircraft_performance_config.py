from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class AircraftPerformanceConfig:
    best_glide_speed_kt: float = 80.0
    glide_ratio: float = 9.0
    glide_reserve_altitude_ft: float = 1000.0

    def __post_init__(self) -> None:
        self._validate_positive(
            self.best_glide_speed_kt,
            "best_glide_speed_kt",
        )

        self._validate_positive(
            self.glide_ratio,
            "glide_ratio",
        )

        self._validate_nonnegative(
            self.glide_reserve_altitude_ft,
            "glide_reserve_altitude_ft",
        )

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> None:
        if not isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{name} must be finite and positive"
            )

    @staticmethod
    def _validate_nonnegative(
        value: float,
        name: str,
    ) -> None:
        if not isfinite(value) or value < 0.0:
            raise ValueError(
                f"{name} must be finite and not negative"
            )