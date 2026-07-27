import pytest

from pyefis.user.blake_pfd.core.airport_glide_analyzer import (
    AirportGlideCandidate,
)
from pyefis.user.blake_pfd.core.emergency_airport_advisor import (
    EmergencyAirportAdvisor,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    ReachableAirportResult,
)
from pyefis.user.blake_pfd.core.reachable_airport_selector import (
    RankedAirportCandidate,
)


def ranked_candidate(
    identifier: str,
    safety_margin_ft: float,
    distance_nm: float = 5.0,
    bearing_deg: float = 90.0,
) -> RankedAirportCandidate:
    candidate = AirportGlideCandidate(
        identifier=identifier,
        distance_nm=distance_nm,
        bearing_deg=bearing_deg,
        airport_elevation_ft=500.0,
        required_glide_ratio=6.0,
        arrival_altitude_ft=(
            500.0 + safety_margin_ft
        ),
        safety_margin_ft=safety_margin_ft,
        reachable=True,
        valid=True,
    )

    return RankedAirportCandidate(
        candidate=candidate,
        score=100.0,
    )


def test_inactive_emergency_returns_normal_advice() -> None:
    advisor = EmergencyAirportAdvisor()

    result = advisor.advise(
        result=None,
        emergency_active=False,
    )

    assert result.severity == "NORMAL"
    assert result.valid is True
    assert result.airport_identifier is None


def test_best_ranked_airport_is_selected() -> None:
    advisor = EmergencyAirportAdvisor()

    pipeline_result = ReachableAirportResult(
        glide_range_nm=10.0,
        ranked=(
            ranked_candidate(
                "KHAO",
                safety_margin_ft=2000.0,
            ),
            ranked_candidate(
                "KDAY",
                safety_margin_ft=1800.0,
            ),
        ),
        valid=True,
    )

    result = advisor.advise(
        pipeline_result,
        emergency_active=True,
    )

    assert result.severity == "NORMAL"
    assert result.airport_identifier == "KHAO"
    assert result.title == "Best Airport: KHAO"
    assert "5.0 NM" in result.message


def test_moderate_margin_creates_caution() -> None:
    advisor = EmergencyAirportAdvisor(
        caution_margin_ft=1500.0,
        warning_margin_ft=750.0,
    )

    pipeline_result = ReachableAirportResult(
        ranked=(
            ranked_candidate(
                "TEST",
                safety_margin_ft=1000.0,
            ),
        ),
        valid=True,
    )

    result = advisor.advise(
        pipeline_result,
        emergency_active=True,
    )

    assert result.severity == "CAUTION"
    assert result.safety_margin_ft == 1000.0


def test_low_margin_creates_warning() -> None:
    advisor = EmergencyAirportAdvisor()

    pipeline_result = ReachableAirportResult(
        ranked=(
            ranked_candidate(
                "TEST",
                safety_margin_ft=500.0,
            ),
        ),
        valid=True,
    )

    result = advisor.advise(
        pipeline_result,
        emergency_active=True,
    )

    assert result.severity == "WARNING"


def test_no_reachable_airport_creates_critical_advice() -> None:
    advisor = EmergencyAirportAdvisor()

    pipeline_result = ReachableAirportResult(
        ranked=(),
        valid=True,
    )

    result = advisor.advise(
        pipeline_result,
        emergency_active=True,
    )

    assert result.severity == "CRITICAL"
    assert result.title == "No Reachable Airport"
    assert result.airport_identifier is None


def test_invalid_pipeline_result_creates_warning() -> None:
    advisor = EmergencyAirportAdvisor()

    pipeline_result = ReachableAirportResult(
        valid=False,
    )

    result = advisor.advise(
        pipeline_result,
        emergency_active=True,
    )

    assert result.severity == "WARNING"
    assert result.title == "Diversion Data Unavailable"
    assert result.valid is False


def test_invalid_thresholds_raise() -> None:
    with pytest.raises(
        ValueError,
        match="caution_margin_ft",
    ):
        EmergencyAirportAdvisor(
            caution_margin_ft=500.0,
            warning_margin_ft=750.0,
        )

    with pytest.raises(
        ValueError,
        match="warning_margin_ft",
    ):
        EmergencyAirportAdvisor(
            warning_margin_ft=-1.0,
        )