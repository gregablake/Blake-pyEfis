from types import SimpleNamespace

from pyefis.user.blake_pfd.core.safe_taxi_display_gate import (
    evaluate_safe_taxi_inputs,
    safe_taxi_takeover_allowed,
)


def watchdog(
    *,
    position_valid=True,
    position_fresh=True,
    air_data_valid=True,
    air_data_fresh=True,
):
    return SimpleNamespace(
        position_valid=position_valid,
        position_fresh=position_fresh,
        air_data_valid=air_data_valid,
        air_data_fresh=air_data_fresh,
    )


def flight_state(
    *,
    airborne=False,
):
    return SimpleNamespace(
        airborne=airborne,
    )


def test_valid_ground_inputs_are_eligible():
    state = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=flight_state(
            airborne=False,
        ),
    )

    assert state.position_fresh is True
    assert state.airborne_inhibit is False


def test_stale_position_fails_closed():
    state = evaluate_safe_taxi_inputs(
        watchdog=watchdog(
            position_fresh=False,
        ),
        flight_state=flight_state(),
    )

    assert state.position_fresh is False


def test_invalid_position_fails_closed():
    state = evaluate_safe_taxi_inputs(
        watchdog=watchdog(
            position_valid=False,
        ),
        flight_state=flight_state(),
    )

    assert state.position_fresh is False


def test_stale_air_data_inhibits_taxi():
    state = evaluate_safe_taxi_inputs(
        watchdog=watchdog(
            air_data_fresh=False,
        ),
        flight_state=flight_state(),
    )

    assert state.airborne_inhibit is True


def test_invalid_air_data_inhibits_taxi():
    state = evaluate_safe_taxi_inputs(
        watchdog=watchdog(
            air_data_valid=False,
        ),
        flight_state=flight_state(),
    )

    assert state.airborne_inhibit is True


def test_airborne_state_inhibits_taxi():
    state = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=flight_state(
            airborne=True,
        ),
    )

    assert state.airborne_inhibit is True


def test_missing_flight_state_fails_closed():
    state = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=None,
    )

    assert state.airborne_inhibit is True


def test_missing_watchdog_attributes_fail_closed():
    state = evaluate_safe_taxi_inputs(
        watchdog=SimpleNamespace(),
        flight_state=flight_state(),
    )

    assert state.position_fresh is False
    assert state.airborne_inhibit is True


def test_takeover_allowed_only_when_every_gate_is_true():
    safety = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=flight_state(),
    )

    assert safe_taxi_takeover_allowed(
        feature_enabled=True,
        auto_switch_enabled=True,
        taxi_active=True,
        safety=safety,
    ) is True


def test_auto_switch_false_prevents_takeover():
    safety = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=flight_state(),
    )

    assert safe_taxi_takeover_allowed(
        feature_enabled=True,
        auto_switch_enabled=False,
        taxi_active=True,
        safety=safety,
    ) is False


def test_feature_false_prevents_takeover():
    safety = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=flight_state(),
    )

    assert safe_taxi_takeover_allowed(
        feature_enabled=False,
        auto_switch_enabled=True,
        taxi_active=True,
        safety=safety,
    ) is False


def test_inactive_taxi_state_prevents_takeover():
    safety = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=flight_state(),
    )

    assert safe_taxi_takeover_allowed(
        feature_enabled=True,
        auto_switch_enabled=True,
        taxi_active=False,
        safety=safety,
    ) is False


def test_bad_position_prevents_takeover_even_if_taxi_active():
    safety = evaluate_safe_taxi_inputs(
        watchdog=watchdog(
            position_fresh=False,
        ),
        flight_state=flight_state(),
    )

    assert safe_taxi_takeover_allowed(
        feature_enabled=True,
        auto_switch_enabled=True,
        taxi_active=True,
        safety=safety,
    ) is False


def test_airborne_inhibit_prevents_takeover_even_if_taxi_active():
    safety = evaluate_safe_taxi_inputs(
        watchdog=watchdog(),
        flight_state=flight_state(
            airborne=True,
        ),
    )

    assert safe_taxi_takeover_allowed(
        feature_enabled=True,
        auto_switch_enabled=True,
        taxi_active=True,
        safety=safety,
    ) is False
