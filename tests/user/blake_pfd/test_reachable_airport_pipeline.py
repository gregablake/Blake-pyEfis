from pyefis.user.blake_pfd.core.glide_calculator import (
    GlideCalculator,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    NearbyAirportRecord,
    ReachableAirportPipeline,
)
from pyefis.user.blake_pfd.core.reachable_airport_selector import (
    ReachableAirportSelector,
)

import pytest


def airport(
    identifier: str,
    distance_nm: float,
    elevation_ft: float = 500.0,
    bearing_deg: float = 0.0,
) -> NearbyAirportRecord:
    return NearbyAirportRecord(
        identifier=identifier,
        distance_nm=distance_nm,
        bearing_deg=bearing_deg,
        elevation_ft=elevation_ft,
    )


def test_pipeline_analyzes_all_airports() -> None:
    pipeline = ReachableAirportPipeline(
        glide_calculator=GlideCalculator(
            glide_ratio=9.0,
            best_glide_speed_kt=80.0,
            reserve_altitude_ft=0.0,
        )
    )

    result = pipeline.evaluate(
        airports=[
            airport("ONE", 3.0),
            airport("TWO", 5.0),
            airport("THREE", 20.0),
        ],
        aircraft_altitude_ft=6000.0,
    )

    assert result.valid is True
    assert len(result.candidates) == 3


def test_pipeline_returns_only_reachable_ranked_airports() -> None:
    pipeline = ReachableAirportPipeline(
        glide_calculator=GlideCalculator(
            glide_ratio=9.0,
            best_glide_speed_kt=80.0,
            reserve_altitude_ft=0.0,
        )
    )

    result = pipeline.evaluate(
        airports=[
            airport("NEAR", 3.0),
            airport("MID", 5.0),
            airport("FAR", 30.0),
        ],
        aircraft_altitude_ft=6000.0,
    )

    identifiers = [
        ranked.candidate.identifier
        for ranked in result.ranked
    ]

    assert "NEAR" in identifiers
    assert "MID" in identifiers
    assert "FAR" not in identifiers


def test_pipeline_limits_results() -> None:
    pipeline = ReachableAirportPipeline(
        glide_calculator=GlideCalculator(
            reserve_altitude_ft=0.0,
        ),
        selector=ReachableAirportSelector(
            maximum_results=2,
        ),
    )

    result = pipeline.evaluate(
        airports=[
            airport("A", 2.0),
            airport("B", 3.0),
            airport("C", 4.0),
        ],
        aircraft_altitude_ft=8000.0,
    )

    assert len(result.ranked) == 2


def test_headwind_reduces_reachable_airports() -> None:
    pipeline = ReachableAirportPipeline(
        glide_calculator=GlideCalculator(
            glide_ratio=9.0,
            best_glide_speed_kt=80.0,
            reserve_altitude_ft=0.0,
        )
    )

    airports = [
        airport(
            "CLOSE",
            4.0,
            bearing_deg=0.0,
        ),
        airport(
            "EDGE",
            7.0,
            bearing_deg=0.0,
        ),
]

    still_air = pipeline.evaluate(
        airports=airports,
        aircraft_altitude_ft=5000.0,
    )

    headwind = pipeline.evaluate(
        airports=airports,
        aircraft_altitude_ft=5000.0,
        wind_speed_kt=35.0,
        wind_from_deg=0.0,
    )

    still_air_ids = {
        ranked.candidate.identifier
        for ranked in still_air.ranked
    }

    headwind_ids = {
        ranked.candidate.identifier
        for ranked in headwind.ranked
    }

    assert still_air_ids >= headwind_ids


def test_empty_airport_list_is_valid() -> None:
    pipeline = ReachableAirportPipeline()

    result = pipeline.evaluate(
        airports=[],
        aircraft_altitude_ft=5000.0,
    )

    assert result.valid is True
    assert result.candidates == ()
    assert result.ranked == ()


def test_invalid_altitude_returns_invalid_result() -> None:
    pipeline = ReachableAirportPipeline()

    result = pipeline.evaluate(
        airports=[
            airport("TEST", 3.0),
        ],
        aircraft_altitude_ft=float("nan"),
    )

    assert result.valid is False
    assert result.ranked == ()


def test_invalid_airport_is_retained_but_not_ranked() -> None:
    pipeline = ReachableAirportPipeline()

    result = pipeline.evaluate(
        airports=[
            NearbyAirportRecord(
                identifier="BAD",
                distance_nm=float("nan"),
                bearing_deg=0.0,
                elevation_ft=500.0,
            )
        ],
        aircraft_altitude_ft=5000.0,
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].valid is False
    assert result.ranked == ()
    
def test_same_wind_affects_opposite_airports_differently() -> None:
    pipeline = ReachableAirportPipeline(
        glide_calculator=GlideCalculator(
            glide_ratio=9.0,
            best_glide_speed_kt=80.0,
            reserve_altitude_ft=0.0,
        )
    )

    result = pipeline.evaluate(
        airports=[
            airport(
                "NORTH",
                distance_nm=6.0,
                bearing_deg=0.0,
            ),
            airport(
                "SOUTH",
                distance_nm=6.0,
                bearing_deg=180.0,
            ),
        ],
        aircraft_altitude_ft=5000.0,
        wind_speed_kt=30.0,
        wind_from_deg=0.0,
    )

    candidates = {
        item.identifier: item
        for item in result.candidates
    }

    assert (
        candidates["SOUTH"].arrival_altitude_ft
        > candidates["NORTH"].arrival_altitude_ft
    )

    assert (
        candidates["SOUTH"].safety_margin_ft
        > candidates["NORTH"].safety_margin_ft
    )


def test_crosswind_does_not_change_forward_glide_range() -> None:
    pipeline = ReachableAirportPipeline(
        glide_calculator=GlideCalculator(
            glide_ratio=9.0,
            best_glide_speed_kt=80.0,
            reserve_altitude_ft=0.0,
        )
    )

    calm = pipeline.evaluate(
        airports=[
            airport(
                "EAST",
                distance_nm=5.0,
                bearing_deg=90.0,
            )
        ],
        aircraft_altitude_ft=5000.0,
    )

    crosswind = pipeline.evaluate(
        airports=[
            airport(
                "EAST",
                distance_nm=5.0,
                bearing_deg=90.0,
            )
        ],
        aircraft_altitude_ft=5000.0,
        wind_speed_kt=30.0,
        wind_from_deg=0.0,
    )

    assert (
        crosswind.candidates[0].arrival_altitude_ft
        == pytest.approx(
            calm.candidates[0].arrival_altitude_ft
        )
    )


def test_invalid_wind_returns_invalid_result() -> None:
    pipeline = ReachableAirportPipeline()

    result = pipeline.evaluate(
        airports=[
            airport("TEST", 3.0),
        ],
        aircraft_altitude_ft=5000.0,
        wind_speed_kt=float("nan"),
        wind_from_deg=0.0,
    )

    assert result.valid is False
    assert result.ranked == ()