"""V12 camera depth, distance haze and urgent alert layout, ridge demo ONLY."""
from math import isfinite
from types import SimpleNamespace
from PyQt6.QtGui import QColor
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def test_v12_strict_opt_in_inherits_v11_and_never_forces_hardware(monkeypatch):
    scene = SimpleNamespace(_v11_ridge_visuals=lambda: True)
    monkeypatch.delenv("BLAKE_PFD_V12_RIDGE_DEPTH", raising=False)
    assert not BlakePfdDemo._v12_ridge_visuals(scene)
    monkeypatch.setenv("BLAKE_PFD_V12_RIDGE_DEPTH", "1")
    assert BlakePfdDemo._v12_ridge_visuals(scene)
    scene._v11_ridge_visuals = lambda: False
    assert not BlakePfdDemo._v12_ridge_visuals(scene)


def _surface():
    # Intentionally shuffled triangles; far face is index 0, near is index 1.
    return SimpleNamespace(
        vertices=(
            SimpleNamespace(north_ft=900.0, east_ft=0.0, up_ft=0.0),
            SimpleNamespace(north_ft=990.0, east_ft=100.0, up_ft=0.0),
            SimpleNamespace(north_ft=990.0, east_ft=-100.0, up_ft=0.0),
            SimpleNamespace(north_ft=100.0, east_ft=0.0, up_ft=0.0),
            SimpleNamespace(north_ft=110.0, east_ft=10.0, up_ft=0.0),
            SimpleNamespace(north_ft=110.0, east_ft=-10.0, up_ft=0.0),
        ),
        triangles=(
            SimpleNamespace(first_index=0, second_index=1, third_index=2),
            SimpleNamespace(first_index=3, second_index=4, third_index=5),
        ),
    )


class MockCamera:
    def prepare_orientation(self, **kwargs):
        return object()

    def world_to_camera_prepared(self, *, north_ft, east_ft, up_ft, orientation):
        return SimpleNamespace(forward_ft=north_ft)


def test_v12_true_forward_depth_paints_far_before_near_regardless_of_index():
    surface = _surface()
    original_triangles = surface.triangles
    # Existing reverse-index ordering is (1,0): near before far.
    order = BlakePfdDemo._v12_depth_draw_order(surface, MockCamera(), 0, 0, 0)
    assert order == (0, 1)
    assert original_triangles is surface.triangles
    assert all(isfinite(v.north_ft) for v in surface.vertices)


def test_v12_invalid_camera_falls_back_to_old_order():
    surface = _surface()
    camera = MockCamera()
    camera.prepare_orientation = lambda **kwargs: None
    assert BlakePfdDemo._v12_depth_draw_order(surface, camera, 0, 0, 0) == (1, 0)
    camera = MockCamera()
    camera.world_to_camera_prepared = lambda **kwargs: None
    assert BlakePfdDemo._v12_depth_draw_order(surface, camera, 0, 0, 0) == (1, 0)


def test_v12_distance_haze_only_adjusts_display_rgb():
    vertices = (
        SimpleNamespace(north_ft=6076.12, east_ft=0.0, elevation_ft=8448.0),
        SimpleNamespace(north_ft=6076.12 * 16.0, east_ft=0.0, elevation_ft=13718.0),
    )
    surface = SimpleNamespace(vertices=vertices)
    originals = (QColor(70, 110, 80), QColor(70, 110, 80))
    adjusted = BlakePfdDemo._v12_depth_colors(surface, originals)
    assert adjusted[0] == originals[0]
    assert adjusted[1] != originals[1]
    assert 0 <= adjusted[1].red() <= 255
    assert [v.elevation_ft for v in vertices] == [8448.0, 13718.0]
    assert BlakePfdDemo._v12_depth_colors(surface, (originals[0],)) == (originals[0],)


def test_v12_warning_banner_keeps_text_clear_of_side_instruments():
    title, message, detail = BlakePfdDemo._v12_warning_text_rects(1024)
    assert title.left() >= 180
    assert message.left() >= 180
    assert detail.left() > message.right()
    assert detail.right() < 830
    assert all(rect.bottom() <= 72 for rect in (title, message, detail))
    assert title.bottom() <= message.top()
