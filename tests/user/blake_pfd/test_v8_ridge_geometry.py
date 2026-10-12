"""V8 opt-in real SRTM ridgeline comparison (simulator only)."""
from math import isclose
from types import SimpleNamespace

from pyefis.user.blake_pfd import sensors_sim
from pyefis.user.blake_pfd.core.synthetic_camera import SyntheticCamera
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
    TerrainSurfaceVertex,
)
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def configure_sensor(monkeypatch):
    settings = SimpleNamespace(simulation=SimpleNamespace(
        reset_counter=0, paused=False, profile="level",
    ))
    monkeypatch.setattr(sensors_sim, "load_config", lambda: settings)
    monkeypatch.setattr(sensors_sim, "monotonic", lambda: 100.0)
    monkeypatch.setenv("BLAKE_PFD_MOUNTAIN_DEMO", "1")
    monkeypatch.setenv("BLAKE_PFD_V6_VISUALS", "1")
    monkeypatch.setenv("BLAKE_PFD_V7_VISUALS", "1")
    monkeypatch.delenv("BLAKE_PFD_SCENIC_DEMO", raising=False)
    return sensors_sim.SimulatedSensorSource()


def test_v8_ridge_lower_camera_and_zero_speed_are_strict_opt_in(monkeypatch):
    sensor = configure_sensor(monkeypatch)
    monkeypatch.delenv("BLAKE_PFD_V8_RIDGE_DEMO", raising=False)
    baseline = sensor.read()
    assert baseline.heading_deg == 240.0
    assert baseline.gps_ground_speed_kt == 0.0
    assert isclose(baseline.static_pressure_pa,
                   sensors_sim.altitude_to_pressure_pa(15000.0))
    monkeypatch.setenv("BLAKE_PFD_V8_RIDGE_DEMO", "1")
    ridge = sensor.read()
    assert ridge.heading_deg == 220.0
    assert ridge.gps_track_deg == 220.0
    assert ridge.gps_ground_speed_kt == 0.0
    assert ridge.differential_pressure_pa == 0.0
    assert (ridge.gps_lat_deg, ridge.gps_lon_deg) == (40.33, -105.53)
    assert isclose(ridge.static_pressure_pa,
                   sensors_sim.altitude_to_pressure_pa(12000.0))


def test_v8_ridge_is_not_enabled_for_cincinnati_or_hardware(monkeypatch):
    monkeypatch.setenv("BLAKE_PFD_V8_RIDGE_DEMO", "1")
    monkeypatch.setenv("BLAKE_PFD_V7_VISUALS", "1")
    monkeypatch.setenv("BLAKE_PFD_V6_VISUALS", "1")
    monkeypatch.delenv("BLAKE_PFD_MOUNTAIN_DEMO", raising=False)
    class FakeScene:
        use_hardware = False
        _v6_visuals_enabled = staticmethod(BlakePfdDemo._v6_visuals_enabled)
        def _v6_mountain_scene(self):
            return BlakePfdDemo._v6_mountain_scene(self)
        def _v8_ridge_scene(self):
            return BlakePfdDemo._v8_ridge_scene(self)
    standalone = FakeScene()
    assert not standalone._v8_ridge_scene()
    standalone.use_hardware = True
    monkeypatch.setenv("BLAKE_PFD_MOUNTAIN_DEMO", "1")
    assert not standalone._v8_ridge_scene()
    standalone.use_hardware = False
    assert standalone._v8_ridge_scene()
    monkeypatch.delenv("BLAKE_PFD_V8_RIDGE_DEMO")
    assert not standalone._v8_ridge_scene()


def peak_surface(*, up_ft=1500.0):
    return TerrainSurface(valid=True, vertices=(
        TerrainSurfaceVertex(
            north_ft=6076.12, east_ft=0.0, up_ft=up_ft,
            latitude_deg=40.25, longitude_deg=-105.53,
            elevation_ft=12000.0 + up_ft,
        ),
        TerrainSurfaceVertex(
            north_ft=12152.24, east_ft=0.0, up_ft=-1500.0,
            latitude_deg=40.16, longitude_deg=-105.53,
            elevation_ft=10500.0,
        ),
    ))


def test_v8_projected_peak_above_horizon_with_actual_camera():
    camera = SyntheticCamera()
    mesh = peak_surface()
    before = tuple(mesh.vertices)
    result = BlakePfdDemo._v8_projected_relief_diagnostic(
        mesh, camera, heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0,
        width_px=1024, height_px=600, near_plane_ft=5.0,
    )
    peak_elevation, visible_count, above_horizon = result
    assert peak_elevation == 13500
    assert visible_count == 2
    assert above_horizon > 100
    assert mesh.vertices == before  # Does not modify terrain or projection.


def test_v8_viewpoint_changes_apparent_peak_not_actual_height():
    camera = SyntheticCamera()
    high = peak_surface(up_ft=-1500.0)
    low = peak_surface(up_ft=1500.0)
    options = dict(
        heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0,
        width_px=1024, height_px=600, near_plane_ft=5.0,
    )
    high_view = BlakePfdDemo._v8_projected_relief_diagnostic(high, camera, **options)
    low_view = BlakePfdDemo._v8_projected_relief_diagnostic(low, camera, **options)
    assert high_view[2] == 0
    assert low_view[2] > 0


def test_v8_missing_or_invalid_terrain_reports_no_peak():
    camera = SyntheticCamera()
    options = dict(
        heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0,
        width_px=1024, height_px=600, near_plane_ft=5.0,
    )
    assert BlakePfdDemo._v8_projected_relief_diagnostic(
        TerrainSurface(), camera, **options,
    ) is None
    assert BlakePfdDemo._v8_projected_relief_diagnostic(
        TerrainSurface(valid=True), camera, **options,
    ) is None
