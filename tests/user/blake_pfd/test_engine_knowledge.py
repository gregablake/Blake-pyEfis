from pyefis.user.blake_pfd.core.engine_knowledge import (
    ENGINE_SCENARIOS,
    EngineScenario,
)


def test_engine_scenarios_are_defined() -> None:
    assert len(ENGINE_SCENARIOS) == 3


def test_all_engine_scenarios_have_required_information() -> None:
    for scenario in ENGINE_SCENARIOS:
        assert isinstance(scenario, EngineScenario)
        assert scenario.name
        assert scenario.symptoms
        assert scenario.likely_causes
        assert scenario.recommended_actions


def test_high_cht_climb_scenario_contains_cooling_guidance() -> None:
    scenario = next(
        item
        for item in ENGINE_SCENARIOS
        if item.name == "High CHT During Climb"
    )

    assert "CHT rising" in scenario.symptoms
    assert "Cooling airflow insufficient" in scenario.likely_causes
    assert "Increase airspeed" in scenario.recommended_actions
    assert "Reduce climb angle" in scenario.recommended_actions


def test_high_oil_temperature_scenario_contains_cooling_actions() -> None:
    scenario = next(
        item
        for item in ENGINE_SCENARIOS
        if item.name == "High Oil Temperature"
    )

    assert "Oil temperature rising" in scenario.symptoms
    assert "Reduce power" in scenario.recommended_actions
    assert "Increase cooling airflow" in scenario.recommended_actions
    assert "Leveling temporarily" in scenario.recommended_actions


def test_cylinder_imbalance_scenario_contains_inspection_guidance() -> None:
    scenario = next(
        item
        for item in ENGINE_SCENARIOS
        if item.name == "Cylinder Imbalance"
    )

    assert "Large CHT spread" in scenario.symptoms
    assert "Mixture imbalance" in scenario.likely_causes
    assert "Verify mixture balance" in scenario.recommended_actions
    assert any(
        action.startswith("Inspect baffling after landing")
        for action in scenario.recommended_actions
    )
