"""V10 real-SRTM ridge visualization (opt-in, not for flight)."""
from types import SimpleNamespace

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QGradient

from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def test_v10_visuals_require_demo_opt_in_and_never_touch_hardware(monkeypatch):
    demo = SimpleNamespace(use_hardware=False, _v8_ridge_scene=lambda: True)
    monkeypatch.delenv("BLAKE_PFD_V10_RIDGE_VISUALS", raising=False)
    assert not BlakePfdDemo._v10_ridge_visuals(demo)
    monkeypatch.setenv("BLAKE_PFD_V10_RIDGE_VISUALS", "1")
    assert BlakePfdDemo._v10_ridge_visuals(demo)
    demo.use_hardware = True
    assert not BlakePfdDemo._v10_ridge_visuals(demo)
    demo.use_hardware = False
    demo._v8_ridge_scene = lambda: False
    assert not BlakePfdDemo._v10_ridge_visuals(demo)


def test_v10_replacement_background_is_earth_gradient_not_solid_brown():
    brush = BlakePfdDemo._v10_ridge_ground_brush(300)
    assert brush.style() == Qt.BrushStyle.LinearGradientPattern
    stops = brush.gradient().stops()
    assert len(stops) == 2
    assert stops[0][0] == 0.0
    assert stops[1][0] == 1.0
    assert stops[0][1] == QColor(80, 112, 104)
    assert stops[1][1] == QColor(43, 74, 67)


def test_v10_diagnostics_fit_clear_of_altitude_tape():
    top, bottom = BlakePfdDemo._v10_ridge_diagnostic_rects(1024, 600)
    for rect in (top, bottom):
        assert rect.left() >= 290
        assert rect.right() < 690  # altitude tape begins ~700 px in ridge mode
        assert rect.top() >= 75   # above any normal banner boundary
        assert rect.bottom() < 130
    assert top.bottom() < bottom.top()


def test_v10_nonhazard_gradient_stays_within_normal_brightness_range():
    points = (
        SimpleNamespace(x_px=100.0, y_px=200.0),
        SimpleNamespace(x_px=250.0, y_px=240.0),
        SimpleNamespace(x_px=160.0, y_px=300.0),
    )
    average = QColor(90, 120, 95)
    brush = BlakePfdDemo._v10_safe_triangle_brush(
        points, average, (0.78, 1.12, 0.93),
    )
    assert brush.style() == Qt.BrushStyle.LinearGradientPattern
    stops = brush.gradient().stops()
    assert len(stops) == 2
    for _, color in stops:
        for input_val, output_val in zip(average.getRgb()[:3], color.getRgb()[:3]):
            assert input_val * 0.84 <= output_val <= input_val * 1.16
    flat = BlakePfdDemo._v10_safe_triangle_brush(
        points, average, (0.98, 0.99, 0.97),
    )
    assert flat.style() == Qt.BrushStyle.SolidPattern
    assert flat.color() == average


def test_v10_uses_original_triangle_geometry_not_replacement_mesh():
    # Shading helpers cannot modify or resample any terrain geometry.
    from inspect import signature
    assert tuple(signature(BlakePfdDemo._v10_safe_triangle_brush).parameters) == (
        "points", "average_color", "vertex_light",
    )
