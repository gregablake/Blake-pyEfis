"""V9 ridge-mode drawing regressions (simulator only)."""
from math import isclose
from types import SimpleNamespace

from PyQt6.QtGui import QBrush, QColor, QImage, QPainter

from pyefis.user.blake_pfd import sensors_sim
from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


def _image_and_painter():
    canvas = QImage(720, 600, QImage.Format.Format_ARGB32)
    canvas.fill(QColor(15, 28, 42))
    painter = QPainter(canvas)
    # Mimic the white brush left behind by another display painter.
    painter.setBrush(QBrush(QColor(255, 255, 255)))
    return canvas, painter


def test_airspeed_outline_never_inherits_solid_white_brush(monkeypatch, qtbot):
    monkeypatch.delenv("BLAKE_PFD_V7_VISUALS", raising=False)
    image, painter = _image_and_painter()
    try:
        BlakePfdDemo.draw_airspeed_tape(
            SimpleNamespace(), painter, SimpleNamespace(ias_kt=0.0), 720, 600,
        )
    finally:
        painter.end()
    # Inside the tape, above all the speed ticks: dark and translucent,
    # not painted white by the border rectangle.
    pixel = image.pixelColor(65, 66)
    assert pixel.red() < 150 and pixel.green() < 150 and pixel.blue() < 150


def test_altitude_outline_never_inherits_solid_white_brush(qtbot):
    image, painter = _image_and_painter()
    fake_widget = SimpleNamespace(
        flight_computer=SimpleNamespace(
            baro_setting_controller=SimpleNamespace(setting_inhg=29.92)
        ),
    )
    try:
        BlakePfdDemo.draw_altitude_tape(
            fake_widget, painter,
            SimpleNamespace(indicated_alt_ft=12000.0), 720, 600,
        )
    finally:
        painter.end()
    pixel = image.pixelColor(642, 66)
    assert pixel.red() < 150 and pixel.green() < 150 and pixel.blue() < 150


def _hsi_has_magenta(*, static_ridge):
    image, painter = _image_and_painter()
    scene = SimpleNamespace(
        _v8_ridge_scene=lambda: static_ridge,
        direct_to_lateral_guidance_state=SimpleNamespace(active=False),
        config=SimpleNamespace(obs=SimpleNamespace(enabled=False)),
    )
    data = SimpleNamespace(
        heading_deg=220.0,
        desired_track_deg=200.0,
        bearing_deg=90.0,
        cdi=0.0,
    )
    try:
        BlakePfdDemo.draw_hsi_compass_rose(scene, painter, data, 720, 600)
    finally:
        painter.end()
    return any(
        image.pixelColor(x, y) == QColor(255, 0, 255)
        for x in range(245, 476, 2) for y in range(330, 570, 2)
    )


def test_static_ridge_hsi_has_no_route_needle_but_normal_hsi_does(qtbot):
    assert not _hsi_has_magenta(static_ridge=True)
    assert _hsi_has_magenta(static_ridge=False)


def test_optional_high_ridge_keeps_position_heading_and_zero_speed(monkeypatch):
    sim_config = SimpleNamespace(simulation=SimpleNamespace(
        reset_counter=0, paused=False, profile="level",
    ))
    monkeypatch.setattr(sensors_sim, "load_config", lambda: sim_config)
    monkeypatch.setattr(sensors_sim, "monotonic", lambda: 100.0)
    for key in (
        "BLAKE_PFD_MOUNTAIN_DEMO", "BLAKE_PFD_V6_VISUALS",
        "BLAKE_PFD_V7_VISUALS", "BLAKE_PFD_V8_RIDGE_DEMO",
    ):
        monkeypatch.setenv(key, "1")
    source = sensors_sim.SimulatedSensorSource()
    monkeypatch.delenv("BLAKE_PFD_V9_HIGH_RIDGE", raising=False)
    low = source.read()
    monkeypatch.setenv("BLAKE_PFD_V9_HIGH_RIDGE", "1")
    high = source.read()
    assert (low.gps_lat_deg, low.gps_lon_deg) == (high.gps_lat_deg, high.gps_lon_deg)
    assert high.heading_deg == low.heading_deg == 220.0
    assert low.gps_ground_speed_kt == high.gps_ground_speed_kt == 0.0
    assert isclose(low.static_pressure_pa, sensors_sim.altitude_to_pressure_pa(12000))
    assert isclose(high.static_pressure_pa, sensors_sim.altitude_to_pressure_pa(15000))
    assert high.differential_pressure_pa == low.differential_pressure_pa == 0.0


def test_high_ridge_requires_full_opt_in(monkeypatch):
    fake = SimpleNamespace(_v8_ridge_scene=lambda: True)
    monkeypatch.delenv("BLAKE_PFD_V9_HIGH_RIDGE", raising=False)
    assert not BlakePfdDemo._v9_high_ridge_scene(fake)
    monkeypatch.setenv("BLAKE_PFD_V9_HIGH_RIDGE", "1")
    assert BlakePfdDemo._v9_high_ridge_scene(fake)
    fake._v8_ridge_scene = lambda: False
    assert not BlakePfdDemo._v9_high_ridge_scene(fake)
