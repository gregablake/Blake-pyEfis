"""V14 simulator-only performance and visual warning regression tests.

No flight-system validation: does not assert the warning algorithm's correctness.
"""
from math import isclose
from types import SimpleNamespace

from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def fake_demo(*, hardware=False, real=True, diagnostics=True, depth=True):
    return SimpleNamespace(
        use_hardware=hardware,
        real_terrain_enabled=real,
        _v13_cincinnati_depth_enabled=lambda: depth and not hardware and real,
        _v13_cincinnati_diagnostics_enabled=lambda: diagnostics and not hardware,
    )


def test_v14_optimization_and_profile_are_separate_and_opt_in(monkeypatch):
    monkeypatch.delenv('BLAKE_PFD_V14_OPTIMIZE', raising=False)
    monkeypatch.delenv('BLAKE_PFD_V14_PROFILE', raising=False)
    assert not BlakePfdDemo._v14_cincinnati_optimize_enabled(fake_demo())
    assert not BlakePfdDemo._v14_cincinnati_profile_enabled(fake_demo())
    monkeypatch.setenv('BLAKE_PFD_V14_OPTIMIZE', '1')
    monkeypatch.setenv('BLAKE_PFD_V14_PROFILE', '1')
    assert BlakePfdDemo._v14_cincinnati_optimize_enabled(fake_demo())
    assert BlakePfdDemo._v14_cincinnati_profile_enabled(fake_demo())
    assert not BlakePfdDemo._v14_cincinnati_optimize_enabled(fake_demo(hardware=True))
    assert not BlakePfdDemo._v14_cincinnati_profile_enabled(fake_demo(hardware=True))
    assert not BlakePfdDemo._v14_cincinnati_optimize_enabled(fake_demo(depth=False))
    assert not BlakePfdDemo._v14_cincinnati_profile_enabled(fake_demo(diagnostics=False))


def test_v14_vertex_lighting_is_computed_once_per_shared_vertex(monkeypatch):
    calls = []

    def record(normal, indices, relative_height):
        calls.append(tuple(indices))
        return 0.8 + 0.2 * relative_height

    monkeypatch.setattr(BlakePfdDemo, '_v7_mountain_light', staticmethod(record))
    elevations = (600.0, 700.0, 800.0, 900.0)
    surface = SimpleNamespace(vertices=tuple(
        SimpleNamespace(elevation_ft=height) for height in elevations
    ))
    normals = ((0.0, 0.0, 1.0),) * 4
    brightness = BlakePfdDemo._v14_vertex_lights(surface, normals, 600.0, 300.0)
    assert len(brightness) == 4
    assert calls == [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)]
    assert brightness[0] == 0.8
    assert isclose(brightness[-1], 1.0)
    assert BlakePfdDemo._v14_vertex_lights(surface, normals[:2], 600.0, 300.0) == ()


def test_v14_gradient_rejects_tiny_flat_and_invalid_polygons():
    pt = lambda x, y: SimpleNamespace(x_px=x, y_px=y)
    large = (pt(0, 0), pt(140, 0), pt(0, 100))
    tiny = (pt(0, 0), pt(20, 0), pt(0, 20))
    method = BlakePfdDemo._v14_gradient_worth_drawing
    assert method(large, (0.75, 0.9, 1.05))
    assert not method(large, (0.9, 0.9, 0.91))
    assert not method(tiny, (0.75, 0.9, 1.05))
    assert not method(large, (0.8, float('nan'), 1.1))
    assert not method(large[:2], (0.75, 0.9, 1.05))


def test_v14_paint_cadence_is_measured_not_inferred_from_terrain_time():
    dummy = SimpleNamespace()
    track = BlakePfdDemo._v14_record_paint
    track(dummy, 100.0, 100.020)
    assert isclose(dummy._v14_paint_ms, 20.0)
    assert dummy._v14_paint_hz is None
    track(dummy, 100.100, 100.125)
    assert isclose(dummy._v14_paint_ms, 25.0)
    assert isclose(dummy._v14_paint_hz, 10.0)
    track(dummy, 100.300, 100.330)
    assert isclose(dummy._v14_paint_hz, 8.5)
    track(dummy, 110.0, 110.03)
    assert dummy._v14_paint_hz is None  # pause/resume is not a zero-FPS trap
    assert BlakePfdDemo._v14_paint_diagnostic_line(None, 10) == 'PFD PAINT RATE N/A'
    assert '8.5 Hz' in BlakePfdDemo._v14_paint_diagnostic_line(8.5, 27.2)


def test_v14_warning_banner_still_displays_original_messages_and_clears(qtbot):
    monkey = SimpleNamespace()
    record = {'texts': [], 'fills': []}

    class Painter:
        def save(self): pass
        def restore(self): pass
        def setPen(self, pen): pass
        def setFont(self, font): pass
        def fillRect(self, *a): record['fills'].append(a)
        def drawText(self, *args): record['texts'].append(args[-1])

    demo = fake_demo()
    demo._v12_ridge_visuals = lambda: False
    demo._v13_cincinnati_warning_rects = BlakePfdDemo._v13_cincinnati_warning_rects
    presentation = SimpleNamespace(
        visible=True, priority='WARNING', title='TERRAIN',
        message='TERRAIN AHEAD', detail='PROJECTED CLEARANCE 156 FT',
    )
    demo.terrain_warning_presentation = presentation
    draw = BlakePfdDemo.draw_terrain_warning_banner
    draw(demo, Painter(), 1024, 600)
    assert record['texts'] == [
        'TERRAIN', 'TERRAIN AHEAD', 'PROJECTED CLEARANCE 156 FT'
    ]
    assert record['fills']
    record['texts'].clear()
    record['fills'].clear()
    presentation.visible = False
    draw(demo, Painter(), 1024, 600)
    assert record == {'texts': [], 'fills': []}
    presentation.visible = True
    presentation.priority = 'CRITICAL'
    presentation.message = 'PULL UP'
    presentation.detail = 'PROJECTED CLEARANCE -353 FT'
    draw(demo, Painter(), 1024, 600)
    assert record['texts'] == [
        'TERRAIN', 'PULL UP', 'PROJECTED CLEARANCE -353 FT'
    ]


def test_v14_diagnostics_do_not_fake_gps_or_draw_stale_location():
    formatter = BlakePfdDemo._v13_diagnostic_text
    pfd = SimpleNamespace(position_valid=True, latitude_deg=39.35,
                          longitude_deg=-84.54)
    watchdog = SimpleNamespace(position_valid=True, position_fresh=False)
    assert formatter(pfd, watchdog, 19.0)[0] == 'GPS UNAVAILABLE'
    watchdog.position_fresh = True
    assert formatter(pfd, watchdog, 19.0)[0].startswith('GPS +39.3500')
