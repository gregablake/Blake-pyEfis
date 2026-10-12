"""Checks for the explicitly opt-in, moving KHAO -> KCVG demo."""
from types import SimpleNamespace

from pyefis.user.blake_pfd import sensors_sim


def _source(monkeypatch):
    config = SimpleNamespace(
        simulation=SimpleNamespace(reset_counter=0, paused=False, profile="level")
    )
    clock = [100.0]
    monkeypatch.setenv("BLAKE_PFD_SCENIC_DEMO", "1")
    monkeypatch.setattr(sensors_sim, "load_config", lambda: config)
    monkeypatch.setattr(sensors_sim, "monotonic", lambda: clock[0])
    return sensors_sim.SimulatedSensorSource(), config, clock


def test_scenic_demo_advances_real_coordinates_and_reports_route_track(monkeypatch):
    source, _, clock = _source(monkeypatch)
    before = source.read()
    clock[0] += 60.0
    after = source.read()
    assert before.gps_lat_deg > after.gps_lat_deg
    assert before.gps_lon_deg > after.gps_lon_deg
    assert 1.5 < source._scenic_progress_nm < 1.9
    assert 190.0 < after.gps_track_deg < 210.0
    assert 2000.0 <= after_altitude_from_sensor(after) <= 2200.0


def after_altitude_from_sensor(data):
    """Pressure altitude from the fixture's standard-atmosphere model."""
    p = data.static_pressure_pa
    return 145366.45 * (1.0 - (p / 101325.0) ** 0.190284)


def test_scenic_pause_holds_position_and_reset_restarts_route(monkeypatch):
    source, config, clock = _source(monkeypatch)
    source.read()
    clock[0] = 140.0
    source.read()
    config.simulation.paused = True
    clock[0] = 200.0
    at_pause = source.read()
    clock[0] = 300.0
    while_paused = source.read()
    assert (at_pause.gps_lat_deg, at_pause.gps_lon_deg) == (
        while_paused.gps_lat_deg, while_paused.gps_lon_deg
    )
    config.simulation.reset_counter += 1
    restarted = source.read()
    assert restarted.gps_lat_deg == sensors_sim._SCENIC_START[0]
    assert abs(restarted.gps_lon_deg - sensors_sim._SCENIC_START[1]) < 1e-10


def test_scenic_mode_is_opt_in_and_default_gps_is_unmodified(monkeypatch):
    source, _, clock = _source(monkeypatch)
    monkeypatch.delenv("BLAKE_PFD_SCENIC_DEMO")
    first = source.read()
    clock[0] += 60.0
    second = source.read()
    assert (first.gps_lat_deg, first.gps_lon_deg) == (39.1031, -84.5120)
    assert (second.gps_lat_deg, second.gps_lon_deg) == (39.1031, -84.5120)


def test_scenic_segment_length_and_endpoints():
    length = sensors_sim._scenic_route_distance_nm()
    assert 18.0 < length < 20.0
    lat, lon, bearing = sensors_sim._scenic_route_position(0.0)
    assert abs(lat - 39.3450) < 1e-8
    assert abs(lon + 84.5320) < 1e-8
    assert 190.0 < bearing < 210.0
    lat, lon, _ = sensors_sim._scenic_route_position(length)
    assert abs(lat - 39.0488) < 1e-8
    assert abs(lon + 84.6678) < 1e-8
