from __future__ import annotations

from pyefis.user.blake_pfd.core.shutdown_marker import (
    ShutdownMarker,
)


def test_missing_marker_is_treated_as_clean(
    tmp_path,
) -> None:
    marker = ShutdownMarker(
        tmp_path / "shutdown.state"
    )

    assert (
        marker.previous_shutdown_clean()
        is True
    )


def test_running_marker_means_unclean_restart(
    tmp_path,
) -> None:
    marker = ShutdownMarker(
        tmp_path / "shutdown.state"
    )

    marker.mark_running()

    assert (
        marker.previous_shutdown_clean()
        is False
    )


def test_clean_marker_means_clean_shutdown(
    tmp_path,
) -> None:
    marker = ShutdownMarker(
        tmp_path / "shutdown.state"
    )

    marker.mark_running()
    marker.mark_clean_shutdown()

    assert (
        marker.previous_shutdown_clean()
        is True
    )


def test_corrupt_marker_is_not_considered_clean(
    tmp_path,
) -> None:
    path = (
        tmp_path
        / "shutdown.state"
    )

    path.write_text(
        "garbage",
        encoding="utf-8",
    )

    marker = ShutdownMarker(
        path
    )

    assert (
        marker.previous_shutdown_clean()
        is False
    )