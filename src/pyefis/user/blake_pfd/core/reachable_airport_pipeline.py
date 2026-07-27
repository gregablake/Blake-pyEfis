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
    ) -> None:
        self.glide_calculator = (
            glide_calculator
            if glide_calculator is not None
            else GlideCalculator()
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

    def evaluate(
        self,
        airports: list[NearbyAirportRecord],
        aircraft_altitude_ft,
        terrain_elevation_ft=0.0,
        headwind_kt=0.0,
        tailwind_kt=0.0,
    ) -> ReachableAirportResult:
        altitude = self._safe_nonnegative(
            aircraft_altitude_ft
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
            return ReachableAirportResult()

        glide = self.glide_calculator.calculate(
            altitude_ft=altitude,
            terrain_elevation_ft=terrain_elevation,
            headwind_kt=headwind,
            tailwind_kt=tailwind,
        )

        if not glide.valid:
            return ReachableAirportResult()

        analyzed: list[AirportGlideCandidate] = []

        for airport in airports:
            candidate = self.analyzer.analyze(
                identifier=airport.identifier,
                distance_nm=airport.distance_nm,
                bearing_deg=airport.bearing_deg,
                airport_elevation_ft=airport.elevation_ft,
                aircraft_altitude_ft=altitude,
                glide=glide,
            )

            analyzed.append(candidate)

        ranked = self.selector.select(
            analyzed
        )

        return ReachableAirportResult(
            glide_range_nm=(
                glide.wind_corrected_range_nm
            ),
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