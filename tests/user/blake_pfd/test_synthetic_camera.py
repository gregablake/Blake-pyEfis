from __future__ import annotations

import pytest

from pyefis.user.blake_pfd.core.synthetic_camera import (
    CameraPoint,
    SyntheticCamera,
)


def test_point_ahead_is_centered() -> None:
    camera = SyntheticCamera()

    point = camera.world_to_camera(
        north_ft=1000.0,
        east_ft=0.0,
        up_ft=0.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )

    assert point is not None
    assert point.right_ft == pytest.approx(0.0)
    assert point.up_ft == pytest.approx(0.0)
    assert point.forward_ft == pytest.approx(1000.0)


def test_east_is_right_when_heading_north() -> None:
    camera = SyntheticCamera()

    point = camera.world_to_camera(
        north_ft=1000.0,
        east_ft=500.0,
        up_ft=0.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )

    assert point is not None
    assert point.right_ft > 0.0


def test_north_is_right_when_heading_west() -> None:
    camera = SyntheticCamera()

    point = camera.world_to_camera(
        north_ft=1000.0,
        east_ft=0.0,
        up_ft=0.0,
        heading_deg=270.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )

    assert point is not None
    assert point.right_ft > 0.0


def test_pitch_up_moves_level_target_down() -> None:
    camera = SyntheticCamera()

    point = camera.world_to_camera(
        north_ft=1000.0,
        east_ft=0.0,
        up_ft=0.0,
        heading_deg=0.0,
        pitch_deg=10.0,
        roll_deg=0.0,
    )

    assert point is not None
    assert point.up_ft < 0.0


def test_roll_right_moves_level_right_target_up() -> None:
    camera = SyntheticCamera()

    point = camera.world_to_camera(
        north_ft=1000.0,
        east_ft=500.0,
        up_ft=0.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=20.0,
    )

    assert point is not None
    assert point.up_ft < 0.0


def test_projection_centers_forward_point() -> None:
    camera = SyntheticCamera()

    projected = camera.project(
        CameraPoint(
            right_ft=0.0,
            up_ft=0.0,
            forward_ft=1000.0,
        ),
        width_px=1280,
        height_px=720,
    )

    assert projected is not None
    assert projected.visible is True
    assert projected.x_px == pytest.approx(640.0)
    assert projected.y_px == pytest.approx(360.0)


def test_projection_moves_right_point_right() -> None:
    camera = SyntheticCamera()

    projected = camera.project(
        CameraPoint(
            right_ft=100.0,
            up_ft=0.0,
            forward_ft=1000.0,
        ),
        width_px=1280,
        height_px=720,
    )

    assert projected is not None
    assert projected.x_px > 640.0


def test_projection_moves_up_point_up() -> None:
    camera = SyntheticCamera()

    projected = camera.project(
        CameraPoint(
            right_ft=0.0,
            up_ft=100.0,
            forward_ft=1000.0,
        ),
        width_px=1280,
        height_px=720,
    )

    assert projected is not None
    assert projected.y_px < 360.0


def test_point_behind_camera_is_hidden() -> None:
    camera = SyntheticCamera()

    projected = camera.project(
        CameraPoint(
            right_ft=0.0,
            up_ft=0.0,
            forward_ft=-100.0,
        ),
        width_px=1280,
        height_px=720,
    )

    assert projected is not None
    assert projected.visible is False


def test_nonfinite_world_input_fails_closed() -> None:
    camera = SyntheticCamera()

    point = camera.world_to_camera(
        north_ft=float("nan"),
        east_ft=0.0,
        up_ft=0.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )

    assert point is None
