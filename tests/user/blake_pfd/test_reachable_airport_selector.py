import pytest

from pyefis.user.blake_pfd.core.airport_glide_analyzer import (
    AirportGlideCandidate,
)
from pyefis.user.blake_pfd.core.reachable_airport_selector import (
    ReachableAirportSelector,
)


def candidate(
    identifier: str,
    distance_nm: float,
    safety_margin_ft: float,
    required_glide_ratio: float,
    reachable: bool = True,
    valid: bool = True,
) -> AirportGlideCandidate:
    return AirportGlideCandidate(
        identifier=identifier,
        distance_nm=distance_nm,
        bearing_deg=0.0,
        airport_elevation_ft=500.0,
        required_glide_ratio=required_glide_ratio,
        arrival_altitude_ft=(
            500.0 + safety_margin_ft
        ),
        safety_margin_ft=safety_margin_ft,
        reachable=reachable,
        valid=valid,
    )


def test_selector_returns_only_reachable_candidates() -> None:
    selector = ReachableAirportSelector()

    results = selector.select(
        [
            candidate(
                "GOOD",
                distance_nm=5.0,
                safety_margin_ft=1500.0,
                required_glide_ratio=6.0,
            ),
            candidate(
                "BAD",
                distance_nm=4.0,
                safety_margin_ft=-200.0,
                required_glide_ratio=12.0,
                reachable=False,
            ),
        ]
    )

    assert len(results) == 1
    assert results[0].candidate.identifier == "GOOD"


def test_selector_rejects_invalid_candidates() -> None:
    selector = ReachableAirportSelector()

    results = selector.select(
        [
            candidate(
                "INVALID",
                distance_nm=2.0,
                safety_margin_ft=2000.0,
                required_glide_ratio=4.0,
                valid=False,
            )
        ]
    )

    assert results == []


def test_selector_applies_minimum_safety_margin() -> None:
    selector = ReachableAirportSelector(
        minimum_safety_margin_ft=1000.0,
    )

    results = selector.select(
        [
            candidate(
                "LOW",
                distance_nm=3.0,
                safety_margin_ft=900.0,
                required_glide_ratio=4.0,
            ),
            candidate(
                "HIGH",
                distance_nm=5.0,
                safety_margin_ft=1200.0,
                required_glide_ratio=5.0,
            ),
        ]
    )

    assert len(results) == 1
    assert results[0].candidate.identifier == "HIGH"


def test_higher_safety_margin_can_beat_shorter_distance() -> None:
    selector = ReachableAirportSelector()

    results = selector.select(
        [
            candidate(
                "CLOSE",
                distance_nm=3.0,
                safety_margin_ft=700.0,
                required_glide_ratio=4.0,
            ),
            candidate(
                "SAFER",
                distance_nm=5.0,
                safety_margin_ft=2500.0,
                required_glide_ratio=5.0,
            ),
        ]
    )

    assert results[0].candidate.identifier == "SAFER"


def test_shorter_airport_wins_when_margins_are_equal() -> None:
    selector = ReachableAirportSelector()

    results = selector.select(
        [
            candidate(
                "FAR",
                distance_nm=8.0,
                safety_margin_ft=1500.0,
                required_glide_ratio=6.0,
            ),
            candidate(
                "NEAR",
                distance_nm=4.0,
                safety_margin_ft=1500.0,
                required_glide_ratio=6.0,
            ),
        ]
    )

    assert results[0].candidate.identifier == "NEAR"


def test_selector_limits_result_count() -> None:
    selector = ReachableAirportSelector(
        maximum_results=2,
    )

    results = selector.select(
        [
            candidate(
                "A",
                distance_nm=2.0,
                safety_margin_ft=2000.0,
                required_glide_ratio=3.0,
            ),
            candidate(
                "B",
                distance_nm=3.0,
                safety_margin_ft=1800.0,
                required_glide_ratio=4.0,
            ),
            candidate(
                "C",
                distance_nm=4.0,
                safety_margin_ft=1600.0,
                required_glide_ratio=5.0,
            ),
        ]
    )

    assert len(results) == 2


def test_score_is_exposed() -> None:
    selector = ReachableAirportSelector()

    results = selector.select(
        [
            candidate(
                "TEST",
                distance_nm=5.0,
                safety_margin_ft=1500.0,
                required_glide_ratio=6.0,
            )
        ]
    )

    assert results[0].score == pytest.approx(
        15.0 - 25.0 - 12.0
    )


def test_invalid_configuration_raises() -> None:
    with pytest.raises(
        ValueError,
        match="minimum_safety_margin_ft",
    ):
        ReachableAirportSelector(
            minimum_safety_margin_ft=-1.0,
        )

    with pytest.raises(
        ValueError,
        match="maximum_results",
    ):
        ReachableAirportSelector(
            maximum_results=0,
        )