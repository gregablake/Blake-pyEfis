from types import SimpleNamespace

from pyefis.user.blake_pfd.core.aircraft_intelligence import (
    AircraftIntelligence,
)


def make_aircraft(
    engine_severity: str = "NORMAL",
    cylinder_imbalance: bool = False,
    prediction_severity: str = "NORMAL",
    cht_time: float | None = None,
    oil_time: float | None = None,
    trend_warning: str = "",
):
    return SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity=engine_severity,
                summary="Engine analysis issue.",
                recommendation="Monitor engine.",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=cylinder_imbalance,
                message="Cylinder imbalance detected.",
            ),
            prediction=SimpleNamespace(
                severity=prediction_severity,
                message="Predicted engine limit.",
                time_to_cht_limit_s=cht_time,
                time_to_oil_temp_limit_s=oil_time,
            ),
            trend=SimpleNamespace(
                warning=trend_warning,
            ),
        )
    )


def test_critical_engine_issue_beats_caution_prediction() -> None:
    intelligence = AircraftIntelligence()

    result = intelligence.analyze(
        make_aircraft(
            engine_severity="CRITICAL",
            prediction_severity="CAUTION",
            cht_time=20.0,
        )
    )

    assert result.severity == "CRITICAL"
    assert result.title == "Engine"


def test_warning_beats_cylinder_caution() -> None:
    intelligence = AircraftIntelligence()

    result = intelligence.analyze(
        make_aircraft(
            engine_severity="WARNING",
            cylinder_imbalance=True,
        )
    )

    assert result.severity == "WARNING"
    assert result.title == "Engine"


def test_prediction_beats_nonurgent_caution_when_same_severity() -> None:
    intelligence = AircraftIntelligence()

    result = intelligence.analyze(
        make_aircraft(
            cylinder_imbalance=True,
            prediction_severity="CAUTION",
            cht_time=25.0,
        )
    )

    assert result.severity == "CAUTION"
    assert result.title == "Predicted Engine Limit"
    assert result.urgency_s == 25.0


def test_shortest_prediction_time_is_used() -> None:
    intelligence = AircraftIntelligence()

    result = intelligence.analyze(
        make_aircraft(
            prediction_severity="CAUTION",
            cht_time=45.0,
            oil_time=18.0,
        )
    )

    assert result.title == "Predicted Engine Limit"
    assert result.urgency_s == 18.0