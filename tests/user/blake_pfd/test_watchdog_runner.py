from __future__ import annotations

from pathlib import Path

import pyefis.user.blake_pfd.watchdog_runner as watchdog_runner


def test_runner_returns_zero_for_healthy_heartbeat(
    tmp_path,
    monkeypatch,
) -> None:
    heartbeat_path = (
        tmp_path
        / "app.heartbeat"
    )

    heartbeat_path.write_text(
        "10.000000",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watchdog_runner,
        "HEARTBEAT_PATH",
        heartbeat_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "monotonic",
        lambda: 11.0,
    )

    result = (
        watchdog_runner.main()
    )

    assert result == 0


def test_runner_returns_one_for_stale_heartbeat(
    tmp_path,
    monkeypatch,
) -> None:
    heartbeat_path = (
        tmp_path
        / "app.heartbeat"
    )

    heartbeat_path.write_text(
        "10.000000",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watchdog_runner,
        "HEARTBEAT_PATH",
        heartbeat_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "monotonic",
        lambda: 13.0,
    )

    result = (
        watchdog_runner.main()
    )

    assert result == 1


def test_runner_returns_one_when_heartbeat_missing(
    tmp_path,
    monkeypatch,
) -> None:
    heartbeat_path = (
        tmp_path
        / "missing.heartbeat"
    )

    monkeypatch.setattr(
        watchdog_runner,
        "HEARTBEAT_PATH",
        heartbeat_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "monotonic",
        lambda: 10.0,
    )

    result = (
        watchdog_runner.main()
    )

    assert result == 1

def test_runner_allows_missing_heartbeat_during_startup_grace(
    tmp_path,
    monkeypatch,
) -> None:
    heartbeat_path = (
        tmp_path
        / "missing.heartbeat"
    )

    startup_marker_path = (
        tmp_path
        / "app.started"
    )

    startup_marker_path.write_text(
        "10.000000",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watchdog_runner,
        "HEARTBEAT_PATH",
        heartbeat_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "STARTUP_MARKER_PATH",
        startup_marker_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "monotonic",
        lambda: 12.0,
    )

    result = (
        watchdog_runner.main()
    )

    assert result == 0


def test_runner_rejects_missing_heartbeat_after_startup_grace(
    tmp_path,
    monkeypatch,
) -> None:
    heartbeat_path = (
        tmp_path
        / "missing.heartbeat"
    )

    startup_marker_path = (
        tmp_path
        / "app.started"
    )

    startup_marker_path.write_text(
        "10.000000",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watchdog_runner,
        "HEARTBEAT_PATH",
        heartbeat_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "STARTUP_MARKER_PATH",
        startup_marker_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "monotonic",
        lambda: 16.0,
    )

    result = (
        watchdog_runner.main()
    )

    assert result == 1

def test_runner_rejects_missing_heartbeat_with_bad_startup_marker(
    tmp_path,
    monkeypatch,
) -> None:
    heartbeat_path = (
        tmp_path
        / "missing.heartbeat"
    )

    startup_marker_path = (
        tmp_path
        / "app.started"
    )

    startup_marker_path.write_text(
        "not-a-number",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        watchdog_runner,
        "HEARTBEAT_PATH",
        heartbeat_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "STARTUP_MARKER_PATH",
        startup_marker_path,
    )

    monkeypatch.setattr(
        watchdog_runner,
        "monotonic",
        lambda: 12.0,
    )

    result = (
        watchdog_runner.main()
    )

    assert result == 1
