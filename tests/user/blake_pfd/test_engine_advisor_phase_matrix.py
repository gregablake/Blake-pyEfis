from types import SimpleNamespace

import pytest

from pyefis.user.blake_pfd.core.engine_advisor import EngineAdvisor
from pyefis.user.blake_pfd.core.flight_phase_guidance import PHASE_GUIDANCE


def build_engine_state(
    message: str,
    *,
    prediction_severity: str = "CAUTION",
    imbalance_detected: bool = False,
):
    return SimpleNamespace(
        prediction=SimpleNamespace(
            severity=prediction_severity,
            message=message,
            confidence=0.8,
        ),
        cylinders=SimpleNamespace(
            imbalance_detected=imbalance_detected,
            hottest_cylinder=3,
            cht_spread_f=70.0,
            egt_spread_f=160.0,
        ),
        health=SimpleNamespace(
            status="NORMAL",
        ),
        data=SimpleNamespace(
            oil_pressure_psi=45.0,
        ),
    )


@pytest.mark.parametrize("phase", PHASE_GUIDANCE.keys())
def test_every_phase_generates_cht_guidance(phase: str) -> None:
    advisor = EngineAdvisor()

    advice = advisor.advise(
        build_engine_state(
            "CHT predicted to reach limit in 30s.",
        ),
        flight_state=SimpleNamespace(
            phase=phase,
        ),
    )

    assert advice.severity == "CAUTION"
    assert advice.title == "CHT Cooling Advisor"
    assert advice.action
    assert advice.reason


@pytest.mark.parametrize("phase", PHASE_GUIDANCE.keys())
def test_every_phase_generates_oil_temperature_guidance(
    phase: str,
) -> None:
    advisor = EngineAdvisor()

    advice = advisor.advise(
        build_engine_state(
            "Oil temperature predicted to reach limit in 20s.",
        ),
        flight_state=SimpleNamespace(
            phase=phase,
        ),
    )

    assert advice.severity == "CAUTION"
    assert advice.title == "Oil Temperature Advisor"
    assert advice.action
    assert advice.reason


@pytest.mark.parametrize("phase", PHASE_GUIDANCE.keys())
def test_every_phase_generates_cylinder_guidance(
    phase: str,
) -> None:
    advisor = EngineAdvisor()

    advice = advisor.advise(
        build_engine_state(
            "No predicted exceedance.",
            prediction_severity="NORMAL",
            imbalance_detected=True,
        ),
        flight_state=SimpleNamespace(
            phase=phase,
        ),
    )

    assert advice.severity == "CAUTION"
    assert advice.title == "Cylinder Balance Advisor"
    assert advice.action
    assert advice.reason