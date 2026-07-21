from types import SimpleNamespace

from pyefis.user.blake_pfd.core.aircraft_intelligence import (
    AircraftIntelligence,
)
from pyefis.user.blake_pfd.core.engine_advisor import EngineAdvisor


def test_climb_cht_prediction_reaches_aircraft_recommendation() -> None:
    advisor = EngineAdvisor()
    intelligence = AircraftIntelligence()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="CHT predicted to reach limit in 30s.",
            confidence=0.85,
            time_to_cht_limit_s=30.0,
            time_to_oil_temp_limit_s=None,
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=False,
        ),
        health=SimpleNamespace(
            status="NORMAL",
        ),
        data=SimpleNamespace(
            oil_pressure_psi=45.0,
        ),
        analysis=SimpleNamespace(
            severity="NORMAL",
            summary="Engine normal.",
            recommendation="Continue.",
        ),
        trend=SimpleNamespace(
            warning="",
        ),
    )

    engine_state.advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CLIMB",
        ),
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    result = intelligence.analyze(aircraft)

    assert result.severity == "CAUTION"
    assert result.title == "CHT Cooling Advisor"
    assert "increase airspeed" in result.recommendation.lower()
    assert result.confidence == 0.85


def test_critical_oil_pressure_reaches_aircraft_recommendation() -> None:
    advisor = EngineAdvisor()
    intelligence = AircraftIntelligence()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="CHT predicted to reach limit in 30s.",
            confidence=0.85,
            time_to_cht_limit_s=30.0,
            time_to_oil_temp_limit_s=None,
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=False,
        ),
        health=SimpleNamespace(
            status="CRITICAL",
            health_score=40,
        ),
        data=SimpleNamespace(
            oil_pressure_psi=10.0,
        ),
        analysis=SimpleNamespace(
            severity="CRITICAL",
            summary="Critical oil pressure.",
            recommendation="Land immediately.",
        ),
        trend=SimpleNamespace(
            warning="",
        ),
    )

    engine_state.advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CLIMB",
        ),
    )

    aircraft = SimpleNamespace(
        engine_state=engine_state,
    )

    result = intelligence.analyze(aircraft)

    assert result.severity == "CRITICAL"
    assert "oil pressure" in result.message.lower()
    assert "landing" in result.recommendation.lower()