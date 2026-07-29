import pytest

from pyefis.user.blake_pfd.core.emergency_airport_advisor import (
    EmergencyAirportAdvice,
)
from pyefis.user.blake_pfd.core.emergency_landing_planner import (
    EmergencyLandingPlanner,
)


def test_inactive_emergency_returns_inactive_plan():
    planner = EmergencyLandingPlanner()

    plan = planner.create_plan(
        advice=None,
        emergency_active=False,
    )

    assert plan.active is False
    assert plan.valid is True
    assert plan.airport_identifier is None


def test_valid_airport_creates_complete_plan():
    planner = EmergencyLandingPlanner(
        best_glide_speed_kt=80.0,
    )

    advice = EmergencyAirportAdvice(
        severity="WARNING",
        title="Best Airport: KHAO",
        airport_identifier="khao",
        distance_nm=4.0,
        bearing_deg=275.0,
        arrival_altitude_ft=1450.0,
        safety_margin_ft=850.0,
        valid=True,
    )

    plan = planner.create_plan(
        advice=advice,
        emergency_active=True,
        ground_speed_kt=80.0,
    )

    assert plan.active is True
    assert plan.valid is True
    assert plan.airport_identifier == "KHAO"
    assert plan.distance_nm == 4.0
    assert plan.bearing_deg == 275.0
    assert plan.estimated_time_sec == pytest.approx(
        180.0
    )
    assert plan.arrival_altitude_ft == 1450.0
    assert plan.safety_margin_ft == 850.0
    assert plan.recommended_speed_kt == 80.0
    assert plan.checklist_name == "ENGINE_FAILURE"
    assert "KHAO" in plan.instruction


def test_missing_ground_speed_uses_best_glide_speed():
    planner = EmergencyLandingPlanner(
        best_glide_speed_kt=80.0,
    )

    advice = EmergencyAirportAdvice(
        airport_identifier="KCVG",
        distance_nm=8.0,
        bearing_deg=180.0,
        valid=True,
    )

    plan = planner.create_plan(
        advice=advice,
        emergency_active=True,
        ground_speed_kt=None,
    )

    assert plan.valid is True
    assert plan.estimated_time_sec == pytest.approx(
        360.0
    )


def test_invalid_advice_returns_fallback_plan():
    planner = EmergencyLandingPlanner()

    advice = EmergencyAirportAdvice(
        valid=False,
    )

    plan = planner.create_plan(
        advice=advice,
        emergency_active=True,
    )

    assert plan.active is True
    assert plan.valid is False
    assert plan.airport_identifier is None
    assert plan.recommended_speed_kt == 80.0
    assert plan.checklist_name == "ENGINE_FAILURE"
    assert "BEST GLIDE" in plan.instruction


def test_missing_airport_fields_returns_off_airport_plan():
    planner = EmergencyLandingPlanner()

    advice = EmergencyAirportAdvice(
        severity="CRITICAL",
        title="No Reachable Airport",
        valid=True,
    )

    plan = planner.create_plan(
        advice=advice,
        emergency_active=True,
    )

    assert plan.active is True
    assert plan.valid is False
    assert plan.airport_identifier is None
    assert "NO REACHABLE AIRPORT" in plan.instruction


def test_bearing_is_normalized():
    planner = EmergencyLandingPlanner()

    advice = EmergencyAirportAdvice(
        airport_identifier="I69",
        distance_nm=2.0,
        bearing_deg=370.0,
        valid=True,
    )

    plan = planner.create_plan(
        advice=advice,
        emergency_active=True,
        ground_speed_kt=60.0,
    )

    assert plan.valid is True
    assert plan.bearing_deg == 10.0


def test_negative_distance_is_rejected():
    planner = EmergencyLandingPlanner()

    advice = EmergencyAirportAdvice(
        airport_identifier="KHAO",
        distance_nm=-1.0,
        bearing_deg=90.0,
        valid=True,
    )

    plan = planner.create_plan(
        advice=advice,
        emergency_active=True,
    )

    assert plan.valid is False
    assert plan.airport_identifier is None


def test_constructor_rejects_invalid_speed():
    with pytest.raises(ValueError):
        EmergencyLandingPlanner(
            best_glide_speed_kt=0.0,
        )


def test_constructor_rejects_empty_checklist():
    with pytest.raises(ValueError):
        EmergencyLandingPlanner(
            checklist_name="",
        )