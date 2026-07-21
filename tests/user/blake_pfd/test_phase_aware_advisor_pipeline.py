from types import SimpleNamespace

from pyefis.user.blake_pfd.core.aircraft_intelligence import (
    AircraftIntelligence,
)
from pyefis.user.blake_pfd.core.engine_advisor import EngineAdvisor


def build_engine_state():
    return SimpleNamespace(
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
            recommendation="Continue normal operation.",
        ),
        trend=SimpleNamespace(
            warning="",
        ),
    )


def test_takeoff_phase_reaches_final_recommendation() -> None:
    advisor = EngineAdvisor()
    intelligence = AircraftIntelligence()
    engine_state = build_engine_state()

    engine_state.advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="TAKEOFF",
        ),
    )

    result = intelligence.analyze(
        SimpleNamespace(
            engine_state=engine_state,
        )
    )

    assert result.severity == "CAUTION"
    assert result.title == "CHT Cooling Advisor"
    assert "continue takeoff" in result.recommendation.lower()
    assert result.confidence == 0.85


def test_climb_phase_reaches_final_recommendation() -> None:
    advisor = EngineAdvisor()
    intelligence = AircraftIntelligence()
    engine_state = build_engine_state()

    engine_state.advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CLIMB",
        ),
    )

    result = intelligence.analyze(
        SimpleNamespace(
            engine_state=engine_state,
        )
    )

    assert result.severity == "CAUTION"
    assert result.title == "CHT Cooling Advisor"
    assert "increase airspeed" in result.recommendation.lower()
    assert "reduce climb angle" in result.recommendation.lower()


def test_cruise_phase_reaches_final_recommendation() -> None:
    advisor = EngineAdvisor()
    intelligence = AircraftIntelligence()
    engine_state = build_engine_state()

    engine_state.advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CRUISE",
        ),
    )

    result = intelligence.analyze(
        SimpleNamespace(
            engine_state=engine_state,
        )
    )

    assert result.severity == "CAUTION"
    assert result.title == "CHT Cooling Advisor"
    assert "lean mixture" in result.recommendation.lower()
    assert "reduce power" in result.recommendation.lower()