"""V7 static mountain visuals: smooth display normals, preserve simulator gates."""
from math import isclose
from types import SimpleNamespace

from pyefis.user.blake_pfd import sensors_sim
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def fake_mesh():
    def v(east, north, up):
        return SimpleNamespace(east_ft=east, north_ft=north,
                               up_ft=up, elevation_ft=10000.0 + up)
    def t(a, b, c):
        return SimpleNamespace(first_index=a, second_index=b, third_index=c)
    return SimpleNamespace(
        vertices=(v(0, 0, 0), v(100, 0, 0),
                  v(0, 100, 20), v(100, 100, 35)),
        triangles=(t(0, 1, 2), t(1, 3, 2)),
    )


def test_v7_vertex_normals_share_smooth_surface_slopes():
    mesh = fake_mesh()
    normals = BlakePfdDemo._v7_vertex_normals(mesh)
    assert len(normals) == len(mesh.vertices)
    assert all(isclose(sum(n*n for n in normal), 1.0, abs_tol=1e-8)
               for normal in normals)
    assert all(normal[2] > 0.0 for normal in normals)
    first_light = BlakePfdDemo._v7_mountain_light(normals, (0, 1, 2), 0.5)
    second_light = BlakePfdDemo._v7_mountain_light(normals, (1, 3, 2), 0.5)
    assert 0.72 <= first_light <= 1.20
    assert 0.72 <= second_light <= 1.20
    assert abs(first_light - second_light) < 0.15


def test_v7_flat_slope_is_natural_and_has_no_division_by_zero():
    mesh = SimpleNamespace(vertices=(
        SimpleNamespace(east_ft=0, north_ft=0, up_ft=0),
        SimpleNamespace(east_ft=0, north_ft=0, up_ft=0),
        SimpleNamespace(east_ft=0, north_ft=0, up_ft=0)),
        triangles=(SimpleNamespace(first_index=0, second_index=1, third_index=2),))
    normals = BlakePfdDemo._v7_vertex_normals(mesh)
    assert normals == ((0.0, 0.0, 1.0),) * 3
    assert 0.72 < BlakePfdDemo._v7_mountain_light(normals, (0, 1, 2), 0.5) < 1.20


def test_v7_stationary_mountain_has_zero_ias_and_frozen_altitude(monkeypatch):
    config = SimpleNamespace(simulation=SimpleNamespace(
        reset_counter=0, paused=False, profile='climb'))
    monkeypatch.setattr(sensors_sim, 'load_config', lambda: config)
    monkeypatch.setattr(sensors_sim, 'monotonic', lambda: 100.0)
    monkeypatch.setenv('BLAKE_PFD_V6_VISUALS', '1')
    monkeypatch.setenv('BLAKE_PFD_V7_VISUALS', '1')
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '1')
    monkeypatch.delenv('BLAKE_PFD_SCENIC_DEMO', raising=False)
    sensor = sensors_sim.SimulatedSensorSource()
    monkeypatch.setattr(sensors_sim, 'monotonic', lambda: 500.0)
    measurement = sensor.read()
    assert measurement.gps_ground_speed_kt == 0.0
    assert measurement.differential_pressure_pa == 0.0
    assert (measurement.gps_lat_deg, measurement.gps_lon_deg) == (40.33, -105.53)
    assert measurement.heading_deg == measurement.gps_track_deg == 240.0
    assert isclose(measurement.static_pressure_pa,
                   sensors_sim.altitude_to_pressure_pa(15000.0))


def test_v7_does_not_change_cincinnati_or_normal_mountain(monkeypatch):
    config = SimpleNamespace(simulation=SimpleNamespace(
        reset_counter=0, paused=False, profile='level'))
    monkeypatch.setattr(sensors_sim, 'load_config', lambda: config)
    monkeypatch.setattr(sensors_sim, 'monotonic', lambda: 100.0)
    monkeypatch.setenv('BLAKE_PFD_V6_VISUALS', '1')
    monkeypatch.setenv('BLAKE_PFD_MOUNTAIN_DEMO', '1')
    monkeypatch.delenv('BLAKE_PFD_V7_VISUALS', raising=False)
    mountain = sensors_sim.SimulatedSensorSource().read()
    assert mountain.differential_pressure_pa > 0.0
    assert mountain.gps_ground_speed_kt == 0.0
    monkeypatch.setenv('BLAKE_PFD_V7_VISUALS', '1')
    monkeypatch.delenv('BLAKE_PFD_MOUNTAIN_DEMO', raising=False)
    monkeypatch.setenv('BLAKE_PFD_SCENIC_DEMO', '1')
    cincinnati = sensors_sim.SimulatedSensorSource().read()
    assert cincinnati.differential_pressure_pa > 0.0
    assert cincinnati.gps_ground_speed_kt > 0.0
