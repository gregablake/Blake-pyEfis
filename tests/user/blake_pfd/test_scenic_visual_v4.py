"""Opt-in V4 illustration rules. No terrain safety computations are modified."""
from types import SimpleNamespace

from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def _point(north, east, elevation):
    return SimpleNamespace(
        north_ft=float(north), east_ft=float(east),
        up_ft=float(elevation - 2000), elevation_ft=float(elevation),
    )


def test_v4_contours_are_interpolated_from_real_vertex_heights():
    a = _point(0, 0, 550)
    b = _point(1000, 0, 750)
    c = _point(0, 1000, 550)
    contours = BlakePfdDemo._v4_contour_segments(a, b, c)
    assert [level for level, _, _ in contours] == [600.0, 700.0]
    for level, start, end in contours:
        assert abs(start[2] - (level - 2000)) < 1e-8
        assert abs(end[2] - (level - 2000)) < 1e-8
    assert contours[0][1][:2] == (250.0, 0.0)
    assert contours[1][1][:2] == (750.0, 0.0)


def test_v4_contours_flat_landscape_has_no_fictitious_levels():
    flat = _point(0, 0, 700)
    assert BlakePfdDemo._v4_contour_segments(flat, flat, flat) == ()


def test_v4_scenic_mode_is_explicitly_opt_in(monkeypatch):
    monkeypatch.delenv("BLAKE_PFD_V4_SCENIC_VISUALS", raising=False)
    assert BlakePfdDemo._v4_visuals_enabled() is False
    monkeypatch.setenv("BLAKE_PFD_V4_SCENIC_VISUALS", "1")
    assert BlakePfdDemo._v4_visuals_enabled() is True
    monkeypatch.setenv("BLAKE_PFD_V4_SCENIC_VISUALS", "0")
    assert BlakePfdDemo._v4_visuals_enabled() is False


def test_v4_non_threats_stay_out_of_instrument_margins():
    inside = BlakePfdDemo._v4_non_threat_inside_scenic_view
    assert inside(500.0, 350.0, 1024, 600)
    assert not inside(100.0, 350.0, 1024, 600)
    assert not inside(920.0, 350.0, 1024, 600)
    assert not inside(500.0, 30.0, 1024, 600)
