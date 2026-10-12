"""V15 consolidated simulator stability/performance regressions.

These tests do NOT validate a terrain/obstacle collision-warning algorithm for flight.
"""
from math import isclose
from types import SimpleNamespace
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def test_v15_measured_slow_paint_cadence_remains_visible():
    # Qt paint loops may be 0.3-0.5 Hz under ARM64 emulation.
    # This is measured; it must NOT be replaced by a fabricated estimate.
    state = SimpleNamespace()
    BlakePfdDemo._v14_record_paint(state, 20.0, 20.200)
    assert state._v14_paint_hz is None
    BlakePfdDemo._v14_record_paint(state, 23.2, 23.4)
    assert isclose(state._v14_paint_hz, 1.0/3.2)
    assert state._v14_paint_ms > 0
    assert '0.3 Hz' in BlakePfdDemo._v14_paint_diagnostic_line(
        state._v14_paint_hz, state._v14_paint_ms)
    BlakePfdDemo._v14_record_paint(state, 85.0, 85.200)
    assert state._v14_paint_hz is None  # >60s pause is not a valid cadence


def test_v15_percentile_handles_invalid_samples_and_bounds():
    fn=BlakePfdDemo._v15_sample_percentile
    assert fn([1.0, 2.0, 3.0, 4.0]) == 4.0
    assert fn([1.0, 2.0, 3.0, 4.0], percentile=0.50) == 3.0
    assert fn([float('nan'), -10.0, float('inf')]) is None
    assert fn([80.0, float('nan'), 15.0]) == 80.0
    assert fn([]) is None


def test_v15_rolling_perf_samples_keep_last_24_and_reject_bad_data():
    state=SimpleNamespace()
    for value in range(40):
        BlakePfdDemo._v15_record_metric(state, 'terrain', value)
    hist=state._v15_metric_terrain
    assert len(hist)==24
    assert hist[0]==16.0 and hist[-1]==39.0
    BlakePfdDemo._v15_record_metric(state, 'terrain', float('inf'))
    BlakePfdDemo._v15_record_metric(state, 'terrain', -1.0)
    assert state._v15_metric_terrain==hist
    state._v15_sample_percentile=BlakePfdDemo._v15_sample_percentile
    assert BlakePfdDemo._v15_metric_p95(state, 'terrain')==38.0
    assert BlakePfdDemo._v15_metric_p95(state, 'none') is None


def test_v15_fast_geometry_never_suppresses_caution_and_requires_lights():
    fn=BlakePfdDemo._v15_fast_normal_skip
    assert fn('NONE', True, (0.8, 0.9, 1.0))
    assert not fn('NONE', False, (0.8,))
    assert not fn('NONE', True, ())
    assert not fn('CAUTION', True, (0.8, 0.9))
    assert fn('WARNING', False, ())
    assert fn('CRITICAL', False, ())
    assert not fn('UNKNOWN', True, (0.8,))


def test_v15_warning_event_only_logs_transitions(capsys):
    demo=SimpleNamespace()
    state=SimpleNamespace(visible=False, priority='NONE', message='')
    recorder=BlakePfdDemo._v15_log_warning_transition
    recorder(demo,state)
    assert capsys.readouterr().out == ''
    state.visible=True
    state.priority='WARNING'
    state.message='TERRAIN AHEAD'
    recorder(demo,state)
    text=capsys.readouterr().out
    assert 'WARNING TERRAIN AHEAD' in text
    recorder(demo,state)
    assert capsys.readouterr().out==''
    state.visible=False
    recorder(demo,state)
    assert 'CLEARED' in capsys.readouterr().out


def test_v15_telemetry_never_converts_terrain_draw_ms_into_fake_fps():
    assert 'P95 250 ms' in BlakePfdDemo._v15_terrain_diagnostic(190.4,250.2)
    assert BlakePfdDemo._v15_terrain_diagnostic(None,250.0)=='TERR DRAW N/A'
    assert BlakePfdDemo._v14_paint_diagnostic_line(None, 190)=='PFD PAINT RATE N/A'
    assert '0.4 Hz' in BlakePfdDemo._v14_paint_diagnostic_line(0.4, 195.0)


def test_v15_warning_banner_bounds_stay_in_central_viewport():
    rects=BlakePfdDemo._v13_cincinnati_warning_rects(1024)
    assert len(rects)==3
    for rect in rects:
        assert rect.left()>=0.19*1024-0.01
        assert rect.right()<=0.80*1024+0.01


def test_v15_gps_freshness_status_is_not_fabricated():
    pfd=SimpleNamespace(position_valid=True, latitude_deg=39.33,
                        longitude_deg=-84.55)
    wd=SimpleNamespace(position_valid=True,position_fresh=False)
    assert BlakePfdDemo._v13_diagnostic_text(pfd,wd,200)[0]=='GPS UNAVAILABLE'
    wd.position_fresh=True
    assert '39.3300' in BlakePfdDemo._v13_diagnostic_text(pfd,wd,200)[0]


def test_v15_dev_flags_never_enable_hardware(monkeypatch):
    demo=SimpleNamespace(
        use_hardware=True, real_terrain_enabled=True,
        _v13_cincinnati_depth_enabled=lambda:False,
        _v13_cincinnati_diagnostics_enabled=lambda:False,
    )
    monkeypatch.setenv('BLAKE_PFD_V14_OPTIMIZE','1')
    monkeypatch.setenv('BLAKE_PFD_V14_PROFILE','1')
    assert not BlakePfdDemo._v14_cincinnati_optimize_enabled(demo)
    assert not BlakePfdDemo._v14_cincinnati_profile_enabled(demo)
