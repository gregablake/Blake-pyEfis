"""V13 scenic Cincinnati display-only gates and diagnostics.

Never a flight qualification test. Test alert thresholds separately.
"""
from types import SimpleNamespace

from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def _demo(*, hardware=False, real_terrain=True):
    return SimpleNamespace(use_hardware=hardware, real_terrain_enabled=real_terrain)


def test_v13_depth_explicit_opt_in_and_not_hardware(monkeypatch):
    monkeypatch.setenv('BLAKE_PFD_SCENIC_DEMO', '1')
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '0')
    monkeypatch.delenv('BLAKE_PFD_V13_CINCINNATI_DEPTH', raising=False)
    method = BlakePfdDemo._v13_cincinnati_depth_enabled
    assert not method(_demo())
    monkeypatch.setenv('BLAKE_PFD_V13_CINCINNATI_DEPTH', '1')
    assert method(_demo())
    assert not method(_demo(hardware=True))
    assert not method(_demo(real_terrain=False))
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '1')
    assert not method(_demo())
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '0')
    monkeypatch.setenv('BLAKE_PFD_SCENIC_DEMO', '0')
    assert not method(_demo())


def test_v13_diagnostics_separately_opted_in(monkeypatch):
    monkeypatch.setenv('BLAKE_PFD_SCENIC_DEMO', '1')
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '0')
    monkeypatch.delenv('BLAKE_PFD_V13_CINCINNATI_DIAGNOSTICS', raising=False)
    method = BlakePfdDemo._v13_cincinnati_diagnostics_enabled
    assert not method(_demo())
    monkeypatch.setenv('BLAKE_PFD_V13_CINCINNATI_DIAGNOSTICS', '1')
    assert method(_demo())
    assert not method(_demo(hardware=True))
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '1')
    assert not method(_demo())


def test_v13_gps_diagnostic_gates_position_freshness_and_formatting():
    display = BlakePfdDemo._v13_diagnostic_text
    good = SimpleNamespace(position_valid=True, position_fresh=True)
    pfd = SimpleNamespace(position_valid=True, latitude_deg=39.123456, longitude_deg=-84.54321)
    gps, duration = display(pfd, good, 12.34)
    assert gps == 'GPS +39.1235, -84.5432'
    assert duration == 'TERR DRAW 12.3 ms'
    good.position_fresh = False
    assert display(pfd, good, 12.34)[0] == 'GPS UNAVAILABLE'
    good.position_fresh = True
    pfd.latitude_deg = 101
    assert display(pfd, good, None) == ('GPS UNAVAILABLE', 'TERR DRAW N/A')
    assert display(None, good, None)[0] == 'GPS UNAVAILABLE'


def test_v13_banner_text_confined_to_central_viewport():
    title, message, detail = BlakePfdDemo._v13_cincinnati_warning_rects(1024)
    for rect in (title, message, detail):
        assert rect.left() >= 1024 * .19 - 1
        assert rect.right() <= 1024 * .80 + 1
        assert rect.top() >= 0
        assert rect.bottom() <= 72
    assert title.right() < detail.left()
    assert message.right() < detail.left()


def test_v13_warning_text_kept_full_and_unmodified(monkeypatch):
    monkeypatch.setenv('BLAKE_PFD_SCENIC_DEMO', '1')
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '0')
    monkeypatch.setenv('BLAKE_PFD_V13_CINCINNATI_DIAGNOSTICS', '1')
    record = {'texts': [], 'fills': []}

    class FakePainter:
        def save(self):
            pass
        def restore(self):
            pass
        def setPen(self, _pen):
            pass
        def setFont(self, _font):
            pass
        def fillRect(self, *args):
            record['fills'].append(args)
        def drawText(self, _rect, _flags, message):
            record['texts'].append(message)

    fake = _demo()
    fake._v12_ridge_visuals = lambda: False
    fake._v13_cincinnati_diagnostics_enabled = lambda: True
    fake._v13_cincinnati_warning_rects = BlakePfdDemo._v13_cincinnati_warning_rects
    fake.terrain_warning_presentation = SimpleNamespace(
        visible=True,
        priority='WARNING',
        title='TERRAIN',
        message='TERRAIN AHEAD',
        detail='PROJECTED CLEARANCE -353 FT',
    )
    BlakePfdDemo.draw_terrain_warning_banner(fake, FakePainter(), 1024, 600)
    assert record['texts'] == [
        'TERRAIN', 'TERRAIN AHEAD', 'PROJECTED CLEARANCE -353 FT'
    ]
    assert record['fills']
