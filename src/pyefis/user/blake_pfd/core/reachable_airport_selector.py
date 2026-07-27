from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from pyefis.user.blake_pfd.core.airport_glide_analyzer import (
    AirportGlideCandidate,
)


@dataclass(frozen=True)
class RankedAirportCandidate:
    candidate: AirportGlideCandidate
    score: float = 0.0


class ReachableAirportSelector:
    def __init__(
        self,
        minimum_safety_margin_ft: float = 0.0,
        maximum_results: int = 5,
    ) -> None:
        if (
            not isfinite(minimum_safety_margin_ft)
            or minimum_safety_margin_ft < 0.0
        ):
            raise ValueError(
                "minimum_safety_margin_ft must be finite "
                "and not negative"
            )

        if maximum_results < 1:
            raise ValueError(
                "maximum_results must be at least 1"
            )

        self.minimum_safety_margin_ft = float(
            minimum_safety_margin_ft
        )

        self.maximum_results = int(
            maximum_results
        )

    def select(
        self,
        candidates: list[AirportGlideCandidate],
    ) -> list[RankedAirportCandidate]:
        ranked: list[RankedAirportCandidate] = []

        for candidate in candidates:
            if not candidate.valid:
                continue

            if not candidate.reachable:
                continue

            if (
                candidate.safety_margin_ft
                < self.minimum_safety_margin_ft
            ):
                continue

            ranked.append(
                RankedAirportCandidate(
                    candidate=candidate,
                    score=self._score(candidate),
                )
            )

        ranked.sort(
            key=self._sort_key,
        )

        return ranked[: self.maximum_results]

    @staticmethod
    def _score(
        candidate: AirportGlideCandidate,
    ) -> float:
        margin_score = (
            candidate.safety_margin_ft
            / 100.0
        )

        distance_penalty = (
            candidate.distance_nm
            * 5.0
        )

        glide_penalty = (
            candidate.required_glide_ratio
            * 2.0
        )

        return (
            margin_score
            - distance_penalty
            - glide_penalty
        )

    @staticmethod
    def _sort_key(
        ranked: RankedAirportCandidate,
    ) -> tuple[float, float, float, str]:
        candidate = ranked.candidate

        return (
            -ranked.score,
            -candidate.safety_margin_ft,
            candidate.distance_nm,
            candidate.identifier,
        )