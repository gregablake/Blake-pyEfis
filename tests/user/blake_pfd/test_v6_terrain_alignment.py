"""V6 simulator-only terrain status and mountain route presentation regression."""
from math import isclose
from types import SimpleNamespace

from pyefis.user.blake_pfd import sensors_sim
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def test_v6_sample_uses_exact_srtm_function_at_gps_location():
    calls = []
    def srtm(lat, lon):
        calls.append((lat, lon))
        return 11420.0
    result = BlakePfdDemo._v6_srtm_ground_sample(
        srtm, 40.33, -105.53, 15048.0
    )
    assert calls == [(40.33, -105.53)]
    assert result == (11420.0, 3628.0)


def test_v6_missing_or_void_srtm_never_substitutes_700_ft():
    sample = BlakePfdDemo._v6_srtm_ground_sample
    assert sample(lambda _lat, _lon: None, 40.33, -105.53, 15048) is None
    assert sample(lambda _lat, _lon: -32768, 40.33, -105.53, 15048) is None
    assert sample(lambda _lat, _lon: float('nan'), 40.33, -105.53, 15048) is None
    assert sample(lambda _lat, _lon: 11500, float('nan'), -105.53, 15048) is None
    assert sample(lambda _lat, _lon: 11500, 40.33, 200, 15048) is None
    assert sample(lambda _lat, _lon: (_ for _ in ()).throw(OSError('tile missing')), 40.33, -105.53, 15048) is None


class FakePainter:
    def __init__(self):
        self.texts = []
    def fillRect(self, *args):
        pass
    def setPen(self, *args):
        pass
    def setBrush(self, *args):
        pass
    def drawRect(self, *args):
        pass
    def setFont(self, *args):
        pass
    def drawText(self, *args):
        self.texts.append(str(args[-1]))


def test_v6_status_paints_actual_ground_and_agl_not_fallback():
    fake = SimpleNamespace(
        _v6_demo_scene=lambda: True,
        _v6_current_srtm_status=lambda: (11420.0, 3628.0),
        real_terrain_enabled=True,
    )
    painter = FakePainter()
    fallback = SimpleNamespace(warning_level='none', terrain_elevation_ft=700.0, clearance_ft=14348.0)
    BlakePfdDemo.draw_terrain_status_box(fake, painter, fallback, 1024, 600)
    assert any('SRTM AT GPS' in t for t in painter.texts)
    assert any('GND 11420 FT AGL 3628 FT' in t for t in painter.texts)
    assert not any('700 FT' in t or '14348' in t for t in painter.texts)


def test_v6_status_says_no_data_instead_of_false_clearance():
    fake = SimpleNamespace(
        _v6_demo_scene=lambda: True,
        _v6_current_srtm_status=lambda: None,
        real_terrain_enabled=True,
    )
    painter = FakePainter()
    fallback = SimpleNamespace(warning_level='none', terrain_elevation_ft=700.0, clearance_ft=14348.0)
    BlakePfdDemo.draw_terrain_status_box(fake, painter, fallback, 1024, 600)
    assert 'GND NO DATA  AGL --' in painter.texts
    assert not any('14348' in t for t in painter.texts)


def test_v6_opt_in_only_non_hardware_scene(monkeypatch):
    monkeypatch.setenv('BLAKE_PFD_V6_VISUALS', '1')
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '1')
    normal = SimpleNamespace(use_hardware=False, _v6_visuals_enabled=lambda: True)
    hardware = SimpleNamespace(use_hardware=True, _v6_visuals_enabled=lambda: True)
    assert BlakePfdDemo._v6_mountain_scene(normal)
    assert not BlakePfdDemo._v6_mountain_scene(hardware)
    monkeypatch.delenv('BLAKE_PFD_MOUNTAIN_DEMO')
    assert not BlakePfdDemo._v6_mountain_scene(normal)


def test_v6_static_mountain_gps_is_zero_kt_only_under_v6(monkeypatch):
    config = SimpleNamespace(simulation=SimpleNamespace(reset_counter=0, paused=False, profile='level'))
    monkeypatch.setattr(sensors_sim, 'load_config', lambda: config)
    monkeypatch.setattr(sensors_sim, 'monotonic', lambda: 100.0)
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '1')
    monkeypatch.delenv('BLAKE_PFD_SCENIC_DEMO', raising=False)
    monkeypatch.delenv('BLAKE_PFD_V6_VISUALS', raising=False)
    sensor = sensors_sim.SimulatedSensorSource()
    before = sensor.read()
    assert before.gps_ground_speed_kt > 0
    monkeypatch.setenv('BLAKE_PFD_V6_VISUALS', '1')
    after = sensor.read()
    assert after.gps_ground_speed_kt == 0.0
    assert (after.gps_lat_deg, after.gps_lon_deg) == (40.33, -105.53)
    assert isclose(after.gps_track_deg, 240)


def test_v6_classification_not_changed_by_status_sampling():
    # Ground sample code must return data, not mutate/replace warning state.
    state = SimpleNamespace(warning_level='red', terrain_elevation_ft=700.0, clearance_ft=14348.0)
    fake = SimpleNamespace(
        _v6_demo_scene=lambda: True,
        _v6_current_srtm_status=lambda: (14700, 348),
        real_terrain_enabled=True,
    )
    BlakePfdDemo.draw_terrain_status_box(fake, FakePainter(), state, 1024, 600)
    assert state.warning_level == 'red'
    assert state.terrain_elevation_ft == 700.0
