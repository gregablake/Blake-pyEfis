from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_advisor import EngineAdvisor
import pytest

def test_normal_engine_returns_normal_advice() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="NORMAL",
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=False,
        ),
        health=SimpleNamespace(
            status="NORMAL",
        ),
        data=SimpleNamespace(
            oil_pressure_psi=50.0,
        ),
    )

    advice = advisor.advise(engine_state)

    assert advice.severity == "NORMAL"
    assert advice.title == "Engine Normal"


def test_prediction_generates_advice() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="CHT predicted to reach limit in 30s.",
            confidence=0.80,
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=False,
        ),
        health=SimpleNamespace(
            status="NORMAL",
        ),
        data=SimpleNamespace(
            oil_pressure_psi=50.0,
        ),
    )

    advice = advisor.advise(engine_state)

    assert advice.severity == "CAUTION"
    assert "Cooling" in advice.title
    assert advice.confidence == 0.80


def test_low_oil_pressure_generates_critical_advice() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="NORMAL",
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=False,
        ),
        health=SimpleNamespace(
            status="CRITICAL",
        ),
        data=SimpleNamespace(
            oil_pressure_psi=10.0,
        ),
    )

    advice = advisor.advise(engine_state)

    assert advice.severity == "CRITICAL"
    assert "Oil Pressure" in advice.title
    
def test_cht_prediction_during_climb_recommends_more_airspeed() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="CHT predicted to reach limit in 30s.",
            confidence=0.85,
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
    )

    flight_state = SimpleNamespace(
        phase="CLIMB",
    )

    advice = advisor.advise(
        engine_state,
        flight_state=flight_state,
    )

    assert advice.severity == "CAUTION"
    assert advice.title == "CHT Cooling Advisor"
    assert "increase airspeed" in advice.action.lower()
    assert "reduce climb angle" in advice.action.lower()
    assert advice.confidence == 0.85


def test_cht_prediction_during_cruise_recommends_reducing_power() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="CHT predicted to reach limit in 30s.",
            confidence=0.75,
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
    )

    flight_state = SimpleNamespace(
        phase="CRUISE",
    )

    advice = advisor.advise(
        engine_state,
        flight_state=flight_state,
    )

    assert advice.severity == "CAUTION"
    assert advice.title == "CHT Cooling Advisor"
    assert "reduce power" in advice.action.lower()
    assert "cooling airflow" in advice.action.lower()
    assert advice.confidence == 0.75
    
def test_oil_temperature_prediction_recommends_cooling_action() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="Oil temperature predicted to reach limit in 20s.",
            confidence=0.90,
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
    )

    advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CLIMB",
        ),
    )

    assert advice.severity == "CAUTION"
    assert advice.title == "Oil Temperature Advisor"
    assert "reduce power" in advice.action.lower()
    assert "increase cooling airflow" in advice.action.lower()
    assert "leveling temporarily" in advice.action.lower()
    assert advice.confidence == 0.90


def test_cylinder_imbalance_generates_balance_advice() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="NORMAL",
            message="No predicted exceedance.",
            confidence=0.0,
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=True,
            hottest_cylinder=3,
            cht_spread_f=72.0,
            egt_spread_f=180.0,
        ),
        health=SimpleNamespace(
            status="NORMAL",
        ),
        data=SimpleNamespace(
            oil_pressure_psi=45.0,
        ),
    )

    advice = advisor.advise(engine_state)

    assert advice.severity == "CAUTION"
    assert advice.title == "Cylinder Balance Advisor"
    assert "cylinder 3" in advice.reason.lower()
    assert "cht spread 72f" in advice.reason.lower()
    assert "egt spread 180f" in advice.reason.lower()
    assert "mixture balance" in advice.action.lower()
    assert advice.confidence == 0.8
    
def test_noncritical_engine_health_generates_general_advice() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="NORMAL",
            message="No predicted exceedance.",
            confidence=0.0,
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=False,
        ),
        health=SimpleNamespace(
            status="CAUTION",
            health_score=72,
        ),
        data=SimpleNamespace(
            oil_pressure_psi=45.0,
        ),
    )

    advice = advisor.advise(engine_state)

    assert advice.severity == "CAUTION"
    assert advice.title == "Engine Health Advisor"
    assert "health score: 72%" in advice.reason.lower()
    assert "review engine instruments" in advice.action.lower()
    assert advice.confidence == 0.9
    
def test_critical_oil_pressure_beats_prediction_caution() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="CHT predicted to reach limit in 30s.",
            confidence=0.85,
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
    )

    advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CLIMB",
        ),
    )

    assert advice.severity == "CRITICAL"
    assert advice.title == "Oil Pressure Advisor"
    assert "immediate landing" in advice.action.lower()
    
def test_missing_engine_scenario_raises_clear_error() -> None:
    advisor = EngineAdvisor()

    with pytest.raises(
        ValueError,
        match="Engine knowledge scenario not found",
    ):
        advisor._scenario("Scenario That Does Not Exist")
        
def test_oil_advisor_uses_knowledge_base_actions() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="Oil temperature predicted to reach limit in 20s.",
            confidence=0.9,
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
    )

    advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CLIMB",
        ),
    )

    assert "Reduce power" in advice.action
    assert "Increase cooling airflow" in advice.action
    assert "Leveling temporarily" in advice.action
    assert "High engine load" in advice.reason
    assert "Reduced cooling" in advice.reason
    
def test_cylinder_advisor_uses_knowledge_base_actions() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="NORMAL",
            message="No predicted exceedance.",
            confidence=0.0,
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=True,
            hottest_cylinder=4,
            cht_spread_f=65.0,
            egt_spread_f=170.0,
        ),
        health=SimpleNamespace(
            status="NORMAL",
        ),
        data=SimpleNamespace(
            oil_pressure_psi=45.0,
        ),
    )

    advice = advisor.advise(engine_state)

    assert advice.severity == "CAUTION"
    assert advice.title == "Cylinder Balance Advisor"

    assert "Cooling imbalance" in advice.reason
    assert "Mixture imbalance" in advice.reason

    assert "Monitor hottest cylinder" in advice.action
    assert "Verify mixture balance" in advice.action
    assert "Check for blockage in cooling airflow" in advice.action
    assert "Inspect baffling after landing" in advice.action
    
def test_cht_climb_advisor_uses_knowledge_base_actions() -> None:
    advisor = EngineAdvisor()

    engine_state = SimpleNamespace(
        prediction=SimpleNamespace(
            severity="CAUTION",
            message="CHT predicted to reach limit in 30s.",
            confidence=0.85,
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
    )

    advice = advisor.advise(
        engine_state,
        flight_state=SimpleNamespace(
            phase="CLIMB",
        ),
    )

    assert advice.severity == "CAUTION"
    assert advice.title == "CHT Cooling Advisor"

    assert "Cooling airflow insufficient" in advice.reason
    assert "Climb angle too steep" in advice.reason

    assert "Increase airspeed" in advice.action
    assert "Reduce climb angle" in advice.action
    assert "Reduce power if necessary" in advice.action

    assert advice.confidence == 0.85