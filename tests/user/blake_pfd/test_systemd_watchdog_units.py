from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

SERVICE_PATH = (
    REPO_ROOT
    / "extras"
    / "extras"
    / "blake-pfd.service"
)

WATCHDOG_SERVICE_PATH = (
    REPO_ROOT
    / "extras"
    / "extras"
    / "blake-pfd-watchdog.service"
)

WATCHDOG_TIMER_PATH = (
    REPO_ROOT
    / "extras"
    / "extras"
    / "blake-pfd-watchdog.timer"
)


def test_pfd_service_has_bounded_recovery() -> None:
    text = SERVICE_PATH.read_text(
        encoding="utf-8",
    )

    assert "Restart=always" in text
    assert "RestartSec=2s" in text
    assert "TimeoutStopSec=3s" in text
    assert "KillMode=control-group" in text


def test_pfd_service_creates_startup_marker() -> None:
    text = SERVICE_PATH.read_text(
        encoding="utf-8",
    )

    assert "app.started" in text
    assert "app.heartbeat" in text
    assert "rm -f" in text


def test_pfd_service_launches_hardware_mode() -> None:
    text = SERVICE_PATH.read_text(
        encoding="utf-8",
    )

    assert (
        "pyefis.user.blake_pfd.pfd_demo --hardware"
        in text
    )


def test_watchdog_service_can_restart_pfd() -> None:
    text = WATCHDOG_SERVICE_PATH.read_text(
        encoding="utf-8",
    )

    assert (
        "pyefis.user.blake_pfd.watchdog_runner"
        in text
    )

    assert (
        "systemctl --user restart blake-pfd.service"
        in text
    )


def test_watchdog_timer_runs_once_per_second() -> None:
    text = WATCHDOG_TIMER_PATH.read_text(
        encoding="utf-8",
    )

    assert "OnUnitActiveSec=1s" in text
    assert (
        "Unit=blake-pfd-watchdog.service"
        in text
    )
