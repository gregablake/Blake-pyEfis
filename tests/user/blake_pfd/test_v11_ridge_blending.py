"""V11 strictly demo-only Gouraud approximation regressions. Not for flight."""
from types import SimpleNamespace
from PyQt6.QtGui import QColor
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def test_v11_opt_in_requires_full_v10_scene_and_demo_switch(monkeypatch):
    scene = SimpleNamespace(_v10_ridge_visuals=lambda: True)
    monkeypatch.delenv("BLAKE_PFD_V11_RIDGE_SHADING", raising=False)
    assert not BlakePfdDemo._v11_ridge_visuals(scene)
    monkeypatch.setenv("BLAKE_PFD_V11_RIDGE_SHADING", "1")
    assert BlakePfdDemo._v11_ridge_visuals(scene)
    scene._v10_ridge_visuals = lambda: False
    assert not BlakePfdDemo._v11_ridge_visuals(scene)


def test_v11_shared_vertex_colors_use_actual_height_normals_and_range():
    vertices = (
        SimpleNamespace(elevation_ft=8448.0, north_ft=0.0, east_ft=0.0),
        SimpleNamespace(elevation_ft=11500.0, north_ft=6076.12 * 4, east_ft=0.0),
        SimpleNamespace(elevation_ft=13718.0, north_ft=6076.12 * 16, east_ft=0.0),
    )
    normals = ((0.0, 0.0, 1.0), (0.0, 0.0, 1.0), (0.0, 0.0, 1.0))
    surface = SimpleNamespace(vertices=vertices)
    colors = BlakePfdDemo._v11_ridge_vertex_colors(surface, normals)
    assert len(colors) == 3
    assert all(isinstance(c, QColor) for c in colors)
    assert all(0 <= component <= 255 for c in colors for component in c.getRgb()[:3])
    assert colors[0] != colors[2]  # mountain rock/vegetation colors vary by real MSL
    assert colors == BlakePfdDemo._v11_ridge_vertex_colors(surface, normals)
    assert [v.elevation_ft for v in surface.vertices] == [8448.0, 11500.0, 13718.0]


def _triangle(edge):
    return (
        SimpleNamespace(x_px=10.0, y_px=10.0),
        SimpleNamespace(x_px=10.0 + edge, y_px=10.0),
        SimpleNamespace(x_px=10.0, y_px=10.0 + edge),
    )


def test_v11_adaptive_screen_subdivision_has_strict_upper_limit():
    assert BlakePfdDemo._v11_ridge_subdivisions(_triangle(12.0)) == 1
    assert BlakePfdDemo._v11_ridge_subdivisions(_triangle(50.0)) == 2
    assert BlakePfdDemo._v11_ridge_subdivisions(_triangle(100.0)) == 3
    assert BlakePfdDemo._v11_ridge_subdivisions(_triangle(200.0)) == 4
    assert BlakePfdDemo._v11_ridge_subdivisions(()) == 1


class FakePainter:
    def __init__(self):
        self.faces = []
        self.brush = None
        self.pen = None

    def setPen(self, pen):
        self.pen = pen

    def setBrush(self, brush):
        self.brush = brush

    def drawConvexPolygon(self, polygon):
        self.faces.append((tuple(polygon), self.brush.color(), self.pen.color()))


def test_v11_gouraud_faces_are_bounded_and_vertex_color_aware():
    colors = (QColor(50, 100, 75), QColor(145, 160, 150), QColor(80, 130, 120))
    for edge, face_count in ((10.0, 1), (50.0, 4), (100.0, 9), (200.0, 16)):
        painter = FakePainter()
        drawn = BlakePfdDemo._v11_draw_smooth_triangle(
            painter, _triangle(edge), colors,
        )
        assert drawn == face_count == len(painter.faces)
        assert all(len(points) == 3 for points, *_ in painter.faces)
        assert all(50 <= fill.red() <= 145 for _, fill, _ in painter.faces)
        assert all(100 <= fill.green() <= 160 for _, fill, _ in painter.faces)
        assert all(75 <= fill.blue() <= 150 for _, fill, _ in painter.faces)
        assert all(fill == border for _, fill, border in painter.faces)
        if face_count > 1:
            assert len(set(fill.name() for _, fill, _ in painter.faces)) > 1


def test_v11_identical_vertex_colors_produce_seamless_flat_result():
    fixed = QColor(100, 130, 110)
    painter = FakePainter()
    assert BlakePfdDemo._v11_draw_smooth_triangle(
        painter, _triangle(200.0), (fixed, fixed, fixed),
    ) == 16
    assert all(fill == fixed for _, fill, _ in painter.faces)
    assert BlakePfdDemo._v11_draw_smooth_triangle(painter, (), ()) == 0
