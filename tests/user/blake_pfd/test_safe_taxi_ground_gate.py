from types import SimpleNamespace

from pyefis.user.blake_pfd.core.safe_taxi_ground_gate import (
    SafeTaxiGroundGate,
)


def flight(
    *,
    gs=0.0,
    ias=0.0,
    vsi=0.0,
):
    return SimpleNamespace(
        ground_speed_kt=gs,
        ias_kt=ias,
        vsi_fpm=vsi,
    )


def state(
    *,
    airborne=False,
    landing_roll=False,
):
    return SimpleNamespace(
        airborne=airborne,
        landing_roll=landing_roll,
    )


def test_startup_does_not_confirm_immediately():
    gate = SafeTaxiGroundGate()

    result = gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=0.0,
    )

    assert result.confirmed is False


def test_stationary_startup_confirms_after_dwell():
    gate = SafeTaxiGroundGate(
        stationary_confirm_seconds=8.0,
    )

    assert gate.update(
        flight=flight(
            gs=0.0,
            ias=0.0,
            vsi=0.0,
        ),
        flight_state=state(),
        inputs_fresh=True,
        now_s=0.0,
    ).confirmed is False

    assert gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=7.9,
    ).confirmed is False

    assert gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=8.0,
    ).confirmed is True


def test_moving_from_program_start_does_not_self_confirm():
    gate = SafeTaxiGroundGate()

    for now_s in (
        0.0,
        5.0,
        10.0,
        20.0,
    ):
        result = gate.update(
            flight=flight(
                gs=12.0,
                ias=10.0,
                vsi=0.0,
            ),
            flight_state=state(),
            inputs_fresh=True,
            now_s=now_s,
        )

        assert result.confirmed is False


def test_airborne_history_is_remembered():
    gate = SafeTaxiGroundGate()

    result = gate.update(
        flight=flight(
            gs=90.0,
            ias=90.0,
            vsi=0.0,
        ),
        flight_state=state(
            airborne=True,
        ),
        inputs_fresh=True,
        now_s=0.0,
    )

    assert result.confirmed is False
    assert result.airborne_seen is True


def test_slow_final_near_airport_does_not_confirm():
    gate = SafeTaxiGroundGate(
        landing_confirm_seconds=3.0,
    )

    # Earlier cruise/flight positively established.
    gate.update(
        flight=flight(
            gs=90.0,
            ias=90.0,
            vsi=-300.0,
        ),
        flight_state=state(
            airborne=True,
        ),
        inputs_fresh=True,
        now_s=0.0,
    )

    # Simulate the flawed shared FlightStateManager
    # now saying "not airborne" on a slow final.
    for now_s in (
        10.0,
        13.0,
        20.0,
    ):
        result = gate.update(
            flight=flight(
                gs=20.0,
                ias=35.0,
                vsi=-250.0,
            ),
            flight_state=state(
                airborne=False,
                landing_roll=True,
            ),
            inputs_fresh=True,
            now_s=now_s,
        )

        assert result.confirmed is False


def test_post_landing_roll_confirms_after_dwell():
    gate = SafeTaxiGroundGate(
        landing_confirm_seconds=3.0,
    )

    gate.update(
        flight=flight(
            gs=90.0,
            ias=90.0,
            vsi=-400.0,
        ),
        flight_state=state(
            airborne=True,
        ),
        inputs_fresh=True,
        now_s=0.0,
    )

    assert gate.update(
        flight=flight(
            gs=20.0,
            ias=30.0,
            vsi=0.0,
        ),
        flight_state=state(
            airborne=False,
            landing_roll=True,
        ),
        inputs_fresh=True,
        now_s=10.0,
    ).confirmed is False

    assert gate.update(
        flight=flight(
            gs=18.0,
            ias=25.0,
            vsi=0.0,
        ),
        flight_state=state(
            airborne=False,
            landing_roll=True,
        ),
        inputs_fresh=True,
        now_s=12.9,
    ).confirmed is False

    assert gate.update(
        flight=flight(
            gs=18.0,
            ias=25.0,
            vsi=0.0,
        ),
        flight_state=state(
            airborne=False,
            landing_roll=True,
        ),
        inputs_fresh=True,
        now_s=13.0,
    ).confirmed is True


def test_excessive_vertical_speed_resets_landing_dwell():
    gate = SafeTaxiGroundGate(
        landing_confirm_seconds=3.0,
    )

    gate.update(
        flight=flight(
            gs=90.0,
            ias=90.0,
        ),
        flight_state=state(
            airborne=True,
        ),
        inputs_fresh=True,
        now_s=0.0,
    )

    gate.update(
        flight=flight(
            gs=20.0,
            ias=30.0,
            vsi=0.0,
        ),
        flight_state=state(
            landing_roll=True,
        ),
        inputs_fresh=True,
        now_s=10.0,
    )

    result = gate.update(
        flight=flight(
            gs=20.0,
            ias=30.0,
            vsi=-300.0,
        ),
        flight_state=state(
            landing_roll=True,
        ),
        inputs_fresh=True,
        now_s=12.0,
    )

    assert result.confirmed is False

    # Dwell must restart, not continue from 10 seconds.
    result = gate.update(
        flight=flight(
            gs=15.0,
            ias=20.0,
            vsi=0.0,
        ),
        flight_state=state(
            landing_roll=True,
        ),
        inputs_fresh=True,
        now_s=13.0,
    )

    assert result.confirmed is False


def test_stale_inputs_fail_closed_and_reset():
    gate = SafeTaxiGroundGate(
        stationary_confirm_seconds=8.0,
    )

    gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=0.0,
    )

    result = gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=False,
        now_s=7.0,
    )

    assert result.confirmed is False

    # Fresh again, but the old dwell may not survive.
    result = gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=8.0,
    )

    assert result.confirmed is False


def test_airborne_immediately_clears_confirmation():
    gate = SafeTaxiGroundGate(
        stationary_confirm_seconds=1.0,
    )

    gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=0.0,
    )

    assert gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=1.0,
    ).confirmed is True

    result = gate.update(
        flight=flight(
            gs=70.0,
            ias=70.0,
            vsi=500.0,
        ),
        flight_state=state(
            airborne=True,
        ),
        inputs_fresh=True,
        now_s=2.0,
    )

    assert result.confirmed is False
    assert result.airborne_seen is True


def test_backward_clock_fails_closed():
    gate = SafeTaxiGroundGate()

    gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=10.0,
    )

    result = gate.update(
        flight=flight(),
        flight_state=state(),
        inputs_fresh=True,
        now_s=9.0,
    )

    assert result.confirmed is False
