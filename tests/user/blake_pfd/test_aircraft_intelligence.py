from pyefis.user.blake_pfd.core.aircraft_intelligence import (
    AircraftIntelligence,
)
from types import SimpleNamespace
import pytest

from pyefis.user.blake_pfd.core.emergency_airport_advisor import (
    EmergencyAirportAdvice,
)
from pyefis.user.blake_pfd.core.emergency_airport_manager import (
    EmergencyAirportState,
)
from pyefis.user.blake_pfd.core.aircraft_performance_config import (
    AircraftPerformanceConfig,
)


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
    
def test_fuel_caution_becomes_aircraft_recommendation() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=None,
        fuel=SimpleNamespace(
            remaining_gal=12.0,
            flow_gph=8.0,
        ),
        navigation=SimpleNamespace(
            distance_nm=90.0,
        ),
        ground_speed_kt=100.0,
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CAUTION"
    assert result.title == "Low Fuel Reserve"
    assert "reserve" in result.message.lower()
    assert result.urgency_s == pytest.approx(
        0.6 * 3600.0,
    )


def test_fuel_warning_beats_engine_caution() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="NORMAL",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
            ),
            prediction=SimpleNamespace(
                severity="NORMAL",
            ),
            advice=SimpleNamespace(
                severity="CAUTION",
                title="CHT Cooling Advisor",
                reason="CHT rising.",
                action="Increase airspeed.",
                confidence=0.8,
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        ),
        fuel=SimpleNamespace(
            remaining_gal=10.0,
            flow_gph=8.0,
        ),
        navigation=SimpleNamespace(
            distance_nm=90.0,
        ),
        ground_speed_kt=100.0,
    )

    result = ai.analyze(aircraft)

    assert result.severity == "WARNING"
    assert result.title == "Fuel Reserve Warning"


def test_critical_fuel_shortfall_beats_engine_warning() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="WARNING",
                summary="High oil temperature.",
                recommendation="Reduce power.",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
            ),
            prediction=SimpleNamespace(
                severity="NORMAL",
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        ),
        fuel=SimpleNamespace(
            remaining_gal=6.0,
            flow_gph=8.0,
        ),
        navigation=SimpleNamespace(
            distance_nm=100.0,
        ),
        ground_speed_kt=100.0,
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CRITICAL"
    assert result.title == (
        "Insufficient Fuel to Destination"
    )


def test_normal_fuel_does_not_replace_engine_advice() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="NORMAL",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
            ),
            prediction=SimpleNamespace(
                severity="NORMAL",
            ),
            advice=SimpleNamespace(
                severity="CAUTION",
                title="CHT Cooling Advisor",
                reason="CHT rising.",
                action="Increase airspeed.",
                confidence=0.8,
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        ),
        fuel=SimpleNamespace(
            remaining_gal=20.0,
            flow_gph=8.0,
        ),
        navigation=SimpleNamespace(
            distance_nm=100.0,
        ),
        ground_speed_kt=100.0,
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CAUTION"
    assert result.title == "CHT Cooling Advisor"
    
def test_emergency_airport_warning_becomes_recommendation() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=None,
        fuel=None,
        navigation=None,
        ground_speed_kt=100.0,
        emergency_airport=EmergencyAirportState(
            advice=EmergencyAirportAdvice(
                severity="WARNING",
                title="Best Airport: KHAO",
                message=(
                    "KHAO is 4.0 NM away with "
                    "1500 ft predicted margin."
                ),
                action="Turn toward KHAO and establish best glide.",
                airport_identifier="KHAO",
                bearing_deg=90.0,
                distance_nm=4.0,
                arrival_altitude_ft=2200.0,
                safety_margin_ft=1500.0,
                valid=True,
            )
        ),
    )

    result = ai.analyze(aircraft)

    assert result.severity == "WARNING"
    assert result.title == "Best Airport: KHAO"
    assert "4.0 NM" in result.message
    assert "best glide" in result.recommendation.lower()

    assert result.urgency_s == pytest.approx(
        4.0 / 80.0 * 3600.0
    )
    
def test_no_reachable_airport_becomes_critical_recommendation() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=None,
        fuel=None,
        navigation=None,
        ground_speed_kt=100.0,
        emergency_airport=EmergencyAirportState(
            advice=EmergencyAirportAdvice(
                severity="CRITICAL",
                title="No Reachable Airport",
                message=(
                    "No airport meets current glide requirements."
                ),
                action=(
                    "Select the best available off-airport "
                    "landing area."
                ),
                valid=True,
            )
        ),
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CRITICAL"
    assert result.title == "No Reachable Airport"
    assert "off-airport" in result.recommendation
    assert result.urgency_s is None
    
def test_inactive_emergency_advice_does_not_replace_engine_advice() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=SimpleNamespace(
            analysis=SimpleNamespace(
                severity="NORMAL",
            ),
            cylinders=SimpleNamespace(
                imbalance_detected=False,
            ),
            prediction=SimpleNamespace(
                severity="NORMAL",
            ),
            advice=SimpleNamespace(
                severity="CAUTION",
                title="CHT Cooling Advisor",
                reason="CHT is rising.",
                action="Increase cooling airflow.",
                confidence=0.8,
            ),
            trend=SimpleNamespace(
                warning="",
            ),
        ),
        fuel=None,
        navigation=None,
        ground_speed_kt=100.0,
        emergency_airport=EmergencyAirportState(
            advice=EmergencyAirportAdvice(
                severity="NORMAL",
                title="No Diversion Required",
                valid=True,
            )
        ),
    )

    result = ai.analyze(aircraft)

    assert result.severity == "CAUTION"
    assert result.title == "CHT Cooling Advisor"
    
def test_emergency_guidance_beats_same_severity_fuel_warning() -> None:
    ai = AircraftIntelligence()

    aircraft = SimpleNamespace(
        engine_state=None,
        fuel=SimpleNamespace(
            remaining_gal=10.0,
            flow_gph=8.0,
        ),
        navigation=SimpleNamespace(
            distance_nm=90.0,
        ),
        ground_speed_kt=100.0,
        emergency_airport=EmergencyAirportState(
            advice=EmergencyAirportAdvice(
                severity="WARNING",
                title="Best Airport: KHAO",
                message="KHAO is the best emergency option.",
                action="Turn toward KHAO.",
                airport_identifier="KHAO",
                distance_nm=4.0,
                valid=True,
            )
        ),
    )

    result = ai.analyze(aircraft)

    assert result.severity == "WARNING"
    assert result.title == "Best Airport: KHAO"
    
    
def test_emergency_airport_urgency_uses_configured_glide_speed() -> None:
    ai = AircraftIntelligence(
        performance_config=AircraftPerformanceConfig(
            best_glide_speed_kt=100.0,
        )
    )

    aircraft = SimpleNamespace(
        engine_state=None,
        fuel=None,
        navigation=None,
        ground_speed_kt=100.0,
        emergency_airport=EmergencyAirportState(
            advice=EmergencyAirportAdvice(
                severity="WARNING",
                title="Best Airport: TEST",
                message="Emergency airport selected.",
                action="Turn toward TEST.",
                airport_identifier="TEST",
                distance_nm=5.0,
                valid=True,
            )
        ),
    )

    result = ai.analyze(aircraft)

    assert result.urgency_s == pytest.approx(
        5.0 / 100.0 * 3600.0
    )