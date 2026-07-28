from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from pyefis.user.blake_pfd.core.airport_glide_analyzer import (
    AirportGlideAnalyzer,
    AirportGlideCandidate,
)
from pyefis.user.blake_pfd.core.glide_calculator import (
    GlideCalculator,
)
from pyefis.user.blake_pfd.core.reachable_airport_selector import (
    RankedAirportCandidate,
    ReachableAirportSelector,
)
from pyefis.user.blake_pfd.core.wind_calculator import (
    WindCalculator,
)
from pyefis.user.blake_pfd.core.aircraft_performance_config import (
    AircraftPerformanceConfig,
)

@dataclass(frozen=True)
class NearbyAirportRecord:
    identifier: str
    distance_nm: float
    bearing_deg: float
    elevation_ft: float


@dataclass(frozen=True)
class ReachableAirportResult:
    glide_range_nm: float = 0.0
    candidates: tuple[AirportGlideCandidate, ...] = ()
    ranked: tuple[RankedAirportCandidate, ...] = ()
    valid: bool = False


class ReachableAirportPipeline:
    def __init__(
        self,
        glide_calculator: GlideCalculator | None = None,
        analyzer: AirportGlideAnalyzer | None = None,
        selector: ReachableAirportSelector | None = None,
        wind_calculator: WindCalculator | None = None,
        performance_config: AircraftPerformanceConfig | None = None,
    ) -> None:
        self.performance_config = (
            performance_config
            if performance_config is not None
            else AircraftPerformanceConfig()
        )

        self.glide_calculator = (
            glide_calculator
            if glide_calculator is not None
            else GlideCalculator(
                glide_ratio=(
                    self.performance_config.glide_ratio
                ),
                best_glide_speed_kt=(
                    self.performance_config.best_glide_speed_kt
                ),
                reserve_altitude_ft=(
                    self.performance_config
                    .glide_reserve_altitude_ft
                ),
            )
        )

        self.analyzer = (
            analyzer
            if analyzer is not None
            else AirportGlideAnalyzer()
        )

        self.selector = (
            selector
            if selector is not None
            else ReachableAirportSelector()
        )

        self.wind_calculator = (
            wind_calculator
            if wind_calculator is not None
            else WindCalculator()
        )

    def evaluate(
        self,
        airports: list[NearbyAirportRecord],
        aircraft_altitude_ft,
        terrain_elevation_ft=0.0,
        wind_speed_kt=0.0,
        wind_from_deg=0.0,
    ) -> ReachableAirportResult:
        altitude = self._safe_nonnegative(
            aircraft_altitude_ft
        )

        terrain_elevation = self._safe_nonnegative(
            terrain_elevation_ft
        )

        safe_wind_speed = self._safe_nonnegative(
            wind_speed_kt
        )

        safe_wind_from = self._safe_angle(
            wind_from_deg
        )

        if (
            altitude is None
            or terrain_elevation is None
            or safe_wind_speed is None
            or safe_wind_from is None
        ):
            return ReachableAirportResult()

        analyzed: list[AirportGlideCandidate] = []
        maximum_glide_range_nm = 0.0

        for airport in airports:
            wind = (
                self.wind_calculator.calculate_components(
                    wind_speed_kt=safe_wind_speed,
                    wind_from_deg=safe_wind_from,
                    course_deg=airport.bearing_deg,
                )
            )

            if not wind.valid:
                analyzed.append(
                    AirportGlideCandidate(
                        identifier=str(
                            airport.identifier
                        ),
                    )
                )
                continue

            glide = self.glide_calculator.calculate(
                altitude_ft=altitude,
                terrain_elevation_ft=(
                    terrain_elevation
                ),
                headwind_kt=wind.headwind_kt,
                tailwind_kt=wind.tailwind_kt,
            )

            maximum_glide_range_nm = max(
                maximum_glide_range_nm,
                glide.wind_corrected_range_nm,
            )

            candidate = self.analyzer.analyze(
                identifier=airport.identifier,
                distance_nm=airport.distance_nm,
                bearing_deg=airport.bearing_deg,
                airport_elevation_ft=(
                    airport.elevation_ft
                ),
                aircraft_altitude_ft=altitude,
                glide=glide,
            )

            analyzed.append(candidate)

        ranked = self.selector.select(
            analyzed
        )

        return ReachableAirportResult(
            glide_range_nm=maximum_glide_range_nm,
            candidates=tuple(analyzed),
            ranked=tuple(ranked),
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