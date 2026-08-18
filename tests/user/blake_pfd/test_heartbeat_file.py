from __future__ import annotations

from pyefis.user.blake_pfd.core.heartbeat_file import (
    HeartbeatFile,
)


def test_first_heartbeat_is_written(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    heartbeat = HeartbeatFile(
        path,
        write_interval_s=0.5,
    )

    written = heartbeat.maybe_write(
        10.0
    )

    assert written is True
    assert path.exists() is True

    assert (
        path.read_text(
            encoding="utf-8"
        )
        == "10.000000"
    )


def test_heartbeat_is_rate_limited(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    heartbeat = HeartbeatFile(
        path,
        write_interval_s=0.5,
    )

    assert (
        heartbeat.maybe_write(
            10.0
        )
        is True
    )

    assert (
        heartbeat.maybe_write(
            10.2
        )
        is False
    )

    assert (
        path.read_text(
            encoding="utf-8"
        )
        == "10.000000"
    )


def test_heartbeat_writes_after_interval(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    heartbeat = HeartbeatFile(
        path,
        write_interval_s=0.5,
    )

    heartbeat.maybe_write(
        10.0
    )

    written = heartbeat.maybe_write(
        10.6
    )

    assert written is True

    assert (
        path.read_text(
            encoding="utf-8"
        )
        == "10.600000"
    )


def test_remove_deletes_heartbeat(
    tmp_path,
) -> None:
    path = tmp_path / "app.heartbeat"

    heartbeat = HeartbeatFile(
        path
    )

    heartbeat.maybe_write(
        10.0
    )

    assert path.exists() is True

    heartbeat.remove()

    assert path.exists() is False


def test_remove_missing_file_is_safe(
    tmp_path,
) -> None:
    heartbeat = HeartbeatFile(
        tmp_path / "missing.heartbeat"
    )

    heartbeat.remove()