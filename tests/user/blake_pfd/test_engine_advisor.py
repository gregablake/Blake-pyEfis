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