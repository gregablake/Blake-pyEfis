from pyefis.user.blake_pfd.core.flight_phase_guidance import (
    PHASE_GUIDANCE,
    PhaseGuidance,
)


def test_expected_flight_phases_exist() -> None:
    assert set(PHASE_GUIDANCE) == {
        "PARKED",
        "RUNUP",
        "TAXI",
        "TAKEOFF",
        "CLIMB",
        "CRUISE",
        "DESCENT",
        "LANDING",
    }


def test_every_phase_has_complete_guidance() -> None:
    for phase_name, guidance in PHASE_GUIDANCE.items():
        assert isinstance(guidance, PhaseGuidance)
        assert guidance.phase == phase_name
        assert guidance.high_cht
        assert guidance.high_oil_temp
        assert guidance.cylinder_imbalance


def test_climb_cht_guidance_recommends_more_cooling_airflow() -> None:
    guidance = PHASE_GUIDANCE["CLIMB"]

    assert "Lower the nose" in guidance.high_cht
    assert "cooling" in guidance.high_cht.lower()


def test_cruise_cht_guidance_recommends_power_or_mixture_change() -> None:
    guidance = PHASE_GUIDANCE["CRUISE"]

    assert "mixture" in guidance.high_cht.lower()
    assert "reduce power" in guidance.high_cht.lower()


def test_takeoff_guidance_does_not_recommend_abrupt_action() -> None:
    guidance = PHASE_GUIDANCE["TAKEOFF"]

    assert "Continue takeoff" in guidance.high_cht
    assert "monitoring" in guidance.high_oil_temp.lower()


def test_descent_guidance_expects_temperature_reduction() -> None:
    guidance = PHASE_GUIDANCE["DESCENT"]

    assert "decrease naturally" in guidance.high_cht
    assert "cooling trend" in guidance.high_oil_temp
    
def test_runup_guidance_prevents_takeoff_with_unstable_engine() -> None:
    guidance = PHASE_GUIDANCE["RUNUP"]

    assert "do not take off" in guidance.high_cht.lower()
    assert "do not take off" in guidance.high_oil_temp.lower()


def test_landing_guidance_prioritizes_aircraft_control() -> None:
    guidance = PHASE_GUIDANCE["LANDING"]

    assert "maintain aircraft control" in guidance.high_cht.lower()
    assert "complete the landing" in guidance.high_oil_temp.lower()


def test_taxi_guidance_keeps_power_low() -> None:
    guidance = PHASE_GUIDANCE["TAXI"]

    assert "reduce power" in guidance.high_cht.lower()
    assert "before takeoff" in guidance.cylinder_imbalance.lower()