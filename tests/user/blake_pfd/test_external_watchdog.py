from __future__ import annotations

from pyefis.user.blake_pfd.core.external_watchdog import (
    ExternalWatchdog,
)


def test_missing_heartbeat_is_stalled(
    tmp_path,
) -> None:
    watchdog = ExternalWatchdog(
        tmp_path / "app.heartbeat",
        stale_after_s=2.0,
    )

    state = watchdog.evaluate(
        10.0
    )

    assert state.stalled is True
    assert state.missing is True
    assert state.message == "HEARTBEAT MISSING"


def test_recent_heartbeat_is_healthy(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    path.write_text(
        "10.000000",
        encoding="utf-8",
    )

    watchdog = ExternalWatchdog(
        path,
        stale_after_s=2.0,
    )

    state = watchdog.evaluate(
        11.0
    )

    assert state.healthy is True
    assert state.stalled is False
    assert state.age_s == 1.0
    assert state.message == "PYEFIS HEALTHY"


def test_old_heartbeat_is_stalled(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    path.write_text(
        "10.000000",
        encoding="utf-8",
    )

    watchdog = ExternalWatchdog(
        path,
        stale_after_s=2.0,
    )

    state = watchdog.evaluate(
        12.1
    )

    assert state.healthy is False
    assert state.stalled is True
    assert state.message == "PYEFIS STALLED"


def test_invalid_heartbeat_is_stalled(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    path.write_text(
        "banana",
        encoding="utf-8",
    )

    watchdog = ExternalWatchdog(
        path,
        stale_after_s=2.0,
    )

    state = watchdog.evaluate(
        10.0
    )

    assert state.stalled is True
    assert state.invalid is True
    assert state.message == "HEARTBEAT INVALID"


def test_backwards_clock_does_not_create_negative_age(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    path.write_text(
        "10.000000",
        encoding="utf-8",
    )

    watchdog = ExternalWatchdog(
        path,
        stale_after_s=2.0,
    )

    state = watchdog.evaluate(
        9.0
    )

    assert state.age_s == 0.0
    assert state.healthy is True