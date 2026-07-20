from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_advisor import EngineAdvisor


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