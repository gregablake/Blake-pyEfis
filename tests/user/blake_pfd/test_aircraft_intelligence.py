from pyefis.user.blake_pfd.core.aircraft_intelligence import (
    AircraftIntelligence,
)
from types import SimpleNamespace


def test_normal_aircraft_returns_normal_recommendation():
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="NORMAL",
                summary="OK",
                recommendation="Continue",
                prediction=SimpleNamespace(
                severity="NORMAL",
                message="No predicted exceedance.",
        ),
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
                message="Balanced",
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        )
    )

    result = ai.analyze(aircraft)

    assert result.severity == "NORMAL"
    assert result.title == "Normal"


def test_engine_warning_becomes_recommendation():
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="WARNING",
                summary="High Oil Temp",
                recommendation="Reduce Power",
                prediction=SimpleNamespace(
                severity="NORMAL",
                message="No predicted exceedance.",
        ),
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
                message="Balanced",
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        )
    )

    result = ai.analyze(aircraft)

    assert result.severity == "WARNING"
    assert "Oil" in result.message
    
def test_engine_prediction_becomes_recommendation():
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="NORMAL",
                summary="Engine normal.",
                recommendation="Continue.",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
                message="Balanced.",
            ),
            prediction=SimpleNamespace(
                severity="CAUTION",
                message="CHT projected to exceed limit soon.",
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        )
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CAUTION"
    assert result.title == "Predicted Engine Limit"
    assert "CHT" in result.message
    
def test_engine_prediction_confidence_is_preserved() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="NORMAL",
                summary="Engine normal.",
                recommendation="Continue.",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
                message="Balanced.",
            ),
            prediction=SimpleNamespace(
                severity="CAUTION",
                message="CHT projected to exceed limit soon.",
                time_to_cht_limit_s=30.0,
                time_to_oil_temp_limit_s=None,
                confidence=0.75,
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        )
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CAUTION"
    assert result.title == "Predicted Engine Limit"
    assert result.urgency_s == 30.0
    assert result.confidence == 0.75
    
def test_engine_advice_becomes_aircraft_recommendation() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="NORMAL",
                summary="Engine normal.",
                recommendation="Continue.",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
                message="Balanced.",
            ),
            prediction=SimpleNamespace(
                severity="NORMAL",
                message="No predicted exceedance.",
                time_to_cht_limit_s=None,
                time_to_oil_temp_limit_s=None,
                confidence=0.0,
            ),
            advice=SimpleNamespace(
                severity="CAUTION",
                title="CHT Cooling Advisor",
                reason="Cylinder temperature is rising during climb.",
                action="Increase airspeed and reduce climb angle.",
                confidence=0.85,
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        )
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CAUTION"
    assert result.title == "CHT Cooling Advisor"
    assert "rising" in result.message.lower()
    assert "increase airspeed" in result.recommendation.lower()
    assert result.confidence == 0.85