from __future__ import annotations

import pytest

from pyefis.user.blake_pfd.core.synthetic_camera import (
    CameraPoint,
    ProjectedPoint,
)
from pyefis.user.blake_pfd.core.synthetic_clipping import (
    clip_camera_polygon_to_near_plane,
    clip_projected_polygon_to_screen,
)


def test_near_plane_keeps_polygon_fully_ahead() -> None:
    points = (
        CameraPoint(-10.0, 0.0, 100.0),
        CameraPoint(10.0, 0.0, 100.0),
        CameraPoint(0.0, 10.0, 100.0),
    )

    clipped = clip_camera_polygon_to_near_plane(
        points,
        near_plane_ft=5.0,
    )

    assert clipped == points


def test_near_plane_clips_one_vertex_behind() -> None:
    points = (
        CameraPoint(-10.0, 0.0, 100.0),
        CameraPoint(10.0, 0.0, 100.0),
        CameraPoint(0.0, 10.0, 0.0),
    )

    clipped = clip_camera_polygon_to_near_plane(
        points,
        near_plane_ft=5.0,
    )

    assert len(clipped) == 4

    for point in clipped:
        assert point.forward_ft >= 5.0


def test_near_plane_clips_two_vertices_behind() -> None:
    points = (
        CameraPoint(0.0, 0.0, 100.0),
        CameraPoint(10.0, 0.0, 0.0),
        CameraPoint(-10.0, 0.0, 0.0),
    )

    clipped = clip_camera_polygon_to_near_plane(
        points,
        near_plane_ft=5.0,
    )

    assert len(clipped) == 3

    for point in clipped:
        assert point.forward_ft >= 5.0


def test_near_plane_removes_polygon_fully_behind() -> None:
    clipped = clip_camera_polygon_to_near_plane(
        (
            CameraPoint(-10.0, 0.0, 0.0),
            CameraPoint(10.0, 0.0, 0.0),
            CameraPoint(0.0, 10.0, -20.0),
        ),
        near_plane_ft=5.0,
    )

    assert clipped == ()


def test_near_plane_interpolates_intersection() -> None:
    clipped = clip_camera_polygon_to_near_plane(
        (
            CameraPoint(
                right_ft=0.0,
                up_ft=0.0,
                forward_ft=10.0,
            ),
            CameraPoint(
                right_ft=10.0,
                up_ft=20.0,
                forward_ft=0.0,
            ),
            CameraPoint(
                right_ft=-10.0,
                up_ft=0.0,
                forward_ft=10.0,
            ),
        ),
        near_plane_ft=5.0,
    )

    intersection = [
        point
        for point in clipped
        if point.forward_ft
        == pytest.approx(5.0)
    ]

    assert len(intersection) == 2


def test_screen_clip_keeps_polygon_fully_inside() -> None:
    points = (
        ProjectedPoint(100.0, 100.0, True),
        ProjectedPoint(200.0, 100.0, True),
        ProjectedPoint(150.0, 200.0, True),
    )

    clipped = clip_projected_polygon_to_screen(
        points,
        width_px=1280,
        height_px=720,
    )

    assert clipped == points


def test_screen_clip_preserves_partially_visible_polygon() -> None:
    clipped = clip_projected_polygon_to_screen(
        (
            ProjectedPoint(
                x_px=-100.0,
                y_px=200.0,
                visible=False,
            ),
            ProjectedPoint(
                x_px=300.0,
                y_px=100.0,
                visible=True,
            ),
            ProjectedPoint(
                x_px=300.0,
                y_px=300.0,
                visible=True,
            ),
        ),
        width_px=1280,
        height_px=720,
    )

    assert len(clipped) >= 3

    for point in clipped:
        assert 0.0 <= point.x_px <= 1280.0
        assert 0.0 <= point.y_px <= 720.0


def test_screen_clip_removes_polygon_fully_outside() -> None:
    clipped = clip_projected_polygon_to_screen(
        (
            ProjectedPoint(
                x_px=-300.0,
                y_px=100.0,
                visible=False,
            ),
            ProjectedPoint(
                x_px=-200.0,
                y_px=200.0,
                visible=False,
            ),
            ProjectedPoint(
                x_px=-100.0,
                y_px=300.0,
                visible=False,
            ),
        ),
        width_px=1280,
        height_px=720,
    )

    assert clipped == ()


def test_invalid_screen_dimensions_fail_closed() -> None:
    clipped = clip_projected_polygon_to_screen(
        (
            ProjectedPoint(
                x_px=100.0,
                y_px=100.0,
                visible=True,
            ),
        ),
        width_px=0,
        height_px=720,
    )

    assert clipped == ()
