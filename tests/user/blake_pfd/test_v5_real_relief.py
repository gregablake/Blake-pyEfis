"""V5 opt-in mountain scene and unchanged projection geometry regression tests."""
from types import SimpleNamespace
from math import isclose
from pyefis.user.blake_pfd import sensors_sim
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo
from pyefis.user.blake_pfd.core.synthetic_camera import SyntheticCamera


def _source(monkeypatch):
    config = SimpleNamespace(
        simulation=SimpleNamespace(reset_counter=0, paused=False, profile="level")
    )
    clock = [100.0]
    monkeypatch.setattr(sensors_sim, "load_config", lambda: config)
    monkeypatch.setattr(sensors_sim, "monotonic", lambda: clock[0])
    return sensors_sim.SimulatedSensorSource(), clock


def _pressure_altitude(pressure):
    return 145366.45 * (1.0 - (pressure / 101325.0) ** 0.190284)


def test_mountain_demo_is_strict_opt_in_and_stationary(monkeypatch):
    monkeypatch.setenv("BLAKE_PFD_MOUNTAIN_DEMO", "1")
    monkeypatch.delenv("BLAKE_PFD_SCENIC_DEMO", raising=False)
    source, clock = _source(monkeypatch)
    first = source.read()
    clock[0] += 120.0
    second = source.read()
    assert (first.gps_lat_deg, first.gps_lon_deg) == (40.33, -105.53)
    assert (second.gps_lat_deg, second.gps_lon_deg) == (40.33, -105.53)
    assert first.gps_track_deg == 240.0
    assert 14930.0 <= _pressure_altitude(second.static_pressure_pa) <= 15070.0


def test_mountain_demo_absent_preserves_standard_gps(monkeypatch):
    monkeypatch.delenv("BLAKE_PFD_MOUNTAIN_DEMO", raising=False)
    monkeypatch.delenv("BLAKE_PFD_SCENIC_DEMO", raising=False)
    source, _ = _source(monkeypatch)
    data = source.read()
    assert (data.gps_lat_deg, data.gps_lon_deg) == (39.1031, -84.5120)


def test_mountain_mode_does_not_override_existing_cincinnati_without_opt_in(monkeypatch):
    monkeypatch.delenv("BLAKE_PFD_MOUNTAIN_DEMO", raising=False)
    monkeypatch.setenv("BLAKE_PFD_SCENIC_DEMO", "1")
    source, _ = _source(monkeypatch)
    data = source.read()
    assert isclose(data.gps_lat_deg, 39.345, abs_tol=1e-7)
    assert isclose(data.gps_lon_deg, -84.532, abs_tol=1e-7)


def test_v5_shading_is_opt_in(monkeypatch):
    monkeypatch.delenv("BLAKE_PFD_V5_REAL_RELIEF", raising=False)
    assert not BlakePfdDemo._v5_visuals_enabled()
    monkeypatch.setenv("BLAKE_PFD_V5_REAL_RELIEF", "1")
    assert BlakePfdDemo._v5_visuals_enabled()
    monkeypatch.setenv("BLAKE_PFD_V5_REAL_RELIEF", "0")
    assert not BlakePfdDemo._v5_visuals_enabled()


def test_true_camera_projection_respects_real_elevation_differences():
    camera = SyntheticCamera()
    orientation = camera.prepare_orientation(
        heading_deg=240.0, pitch_deg=0.0, roll_deg=0.0
    )
    projection = camera.prepare_projection(width_px=1024, height_px=600)
    # Two ground heights directly ahead at the same distance. The higher
    # point must appear higher on screen; no vertical exaggeration in camera.
    low = camera.world_to_camera_prepared(
        north_ft=-5000.0, east_ft=-8660.2540378, up_ft=-6000.0,
        orientation=orientation,
    )
    high = camera.world_to_camera_prepared(
        north_ft=-5000.0, east_ft=-8660.2540378, up_ft=-1000.0,
        orientation=orientation,
    )
    pl = camera.project_prepared(low, projection=projection)
    ph = camera.project_prepared(high, projection=projection)
    assert pl is not None and ph is not None
    assert ph.y_px < pl.y_px
    assert isclose(pl.x_px, ph.x_px, abs_tol=1e-6)
