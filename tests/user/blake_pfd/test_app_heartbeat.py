from pyefis.user.blake_pfd.core.app_heartbeat import (
    AppHeartbeat,
)


def test_heartbeat_not_started_is_stalled() -> None:
    heartbeat = AppHeartbeat(
        stall_after_s=2.0,
    )

    state = heartbeat.evaluate(
        10.0
    )

    assert state.stalled is True
    assert state.healthy is False
    assert (
        state.message
        == "APP HEARTBEAT NOT STARTED"
    )


def test_recent_heartbeat_is_healthy() -> None:
    heartbeat = AppHeartbeat(
        stall_after_s=2.0,
    )

    heartbeat.beat(
        10.0
    )

    state = heartbeat.evaluate(
        11.0
    )

    assert state.healthy is True
    assert state.stalled is False
    assert state.age_s == 1.0


def test_old_heartbeat_is_stalled() -> None:
    heartbeat = AppHeartbeat(
        stall_after_s=2.0,
    )

    heartbeat.beat(
        10.0
    )

    state = heartbeat.evaluate(
        12.1
    )

    assert state.healthy is False
    assert state.stalled is True
    assert state.message == "APP LOOP STALLED"


def test_backwards_clock_does_not_create_negative_age() -> None:
    heartbeat = AppHeartbeat(
        stall_after_s=2.0,
    )

    heartbeat.beat(
        10.0
    )

    state = heartbeat.evaluate(
        9.0
    )

    assert state.age_s == 0.0
    assert state.healthy is True


def test_new_heartbeat_recovers_after_stall() -> None:
    heartbeat = AppHeartbeat(
        stall_after_s=2.0,
    )

    heartbeat.beat(
        10.0
    )

    stalled = heartbeat.evaluate(
        13.0
    )

    assert stalled.stalled is True

    heartbeat.beat(
        13.1
    )

    recovered = heartbeat.evaluate(
        13.2
    )

    assert recovered.healthy is True
    assert recovered.stalled is False