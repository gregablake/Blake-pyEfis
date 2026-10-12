"""Regression tests for the V15 full-screen MAP page contract.

Display/navigation tests only; not validated for flight or airport data completeness.
"""
from types import SimpleNamespace

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter

from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


class FakePainter:
    def __init__(self):
        self.messages = []

    def save(self):
        pass

    def restore(self):
        pass

    def setPen(self, _pen):
        pass

    def setFont(self, _font):
        pass

    def drawText(self, *args):
        self.messages.append(args[-1])


def make_demo(*, fresh=True):
    calls = []
    state = SimpleNamespace(airports=[], range_nm=25.0)
    demo = SimpleNamespace(
        sensor_watchdog_state=SimpleNamespace(position_valid=True, position_fresh=fresh),
        map_airport_markers=['old-stale-marker'],
        map_range_nm=25.0,
        database=object(),
        moving_map=SimpleNamespace(update=lambda **kw: calls.append(kw) or state),
        draw_moving_map_overlay=lambda *args, **kw: calls.append(('overlay', kw)),
    )
    pfd = SimpleNamespace(position_valid=True, latitude_deg=39.3,
                          longitude_deg=-84.5, track_deg=200.0)
    return demo, pfd, calls


def test_map_page_both_required_draw_methods_exist():
    assert callable(getattr(BlakePfdDemo, 'draw_moving_map', None))
    assert callable(getattr(BlakePfdDemo, 'draw_touch_map_controls', None))


def test_stale_gps_must_not_refresh_moving_map_or_old_airport_markers():
    demo, pfd, calls = make_demo(fresh=False)
    painter = FakePainter()
    BlakePfdDemo.draw_moving_map(demo, painter, pfd, 1024, 600)
    assert not calls
    assert demo.map_airport_markers == []
    assert 'MAP POSITION UNAVAILABLE' in painter.messages
    demo, pfd, calls = make_demo()
    pfd.position_valid = False
    BlakePfdDemo.draw_moving_map(demo, FakePainter(), pfd, 1024, 600)
    assert not calls


def test_fresh_gps_uses_existing_map_computer_at_actual_position():
    demo, pfd, calls = make_demo()
    BlakePfdDemo.draw_moving_map(demo, FakePainter(), pfd, 1024, 600)
    assert calls[0]['aircraft_lat'] == 39.3
    assert calls[0]['aircraft_lon'] == -84.5
    assert calls[0]['range_nm'] == 25.0
    assert calls[1] == ('overlay', {'full_page': True})


def test_full_map_page_and_touch_controls_paint_without_crash(qtbot, tmp_path):
    widget = BlakePfdDemo(use_hardware=False, baro_state_path=tmp_path / 'baro.json')
    widget.timer.stop()
    qtbot.addWidget(widget)
    widget.pfd = SimpleNamespace(position_valid=True, latitude_deg=39.3,
                                 longitude_deg=-84.5, track_deg=200.0,
                                 ground_speed_kt=0.0)
    widget.sensor_watchdog_state = SimpleNamespace(position_valid=True,
                                                   position_fresh=True)
    widget.moving_map.update = lambda **kwargs: SimpleNamespace(
        airports=[], range_nm=25.0,
    )
    widget.page_manager.set_page('MAP')
    canvas = QImage(1024, 600, QImage.Format.Format_ARGB32)
    canvas.fill(Qt.GlobalColor.black)
    painter = QPainter(canvas)
    try:
        widget.map_page.draw(painter, widget, 1024, 600)
        widget.draw_touch_navigation(painter, 1024, 600)
    finally:
        painter.end()
    buttons = widget.touch_map_state.buttons
    assert {button.key for button in buttons} == {
        'zoom_in', 'zoom_out', 'center', 'orientation'
    }
    for button in buttons:
        cx = button.bounds.x + button.bounds.width / 2
        cy = button.bounds.y + button.bounds.height / 2
        assert widget.touch_map_controls.action_for_touch(
            point_x=cx, point_y=cy
        ) == button.key
    assert any(button.page_name == 'PFD' for button in widget.touch_navigation_state.buttons)
