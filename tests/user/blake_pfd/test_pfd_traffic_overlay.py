from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPolygonF

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)
from pyefis.user.blake_pfd.stratux_reader import (
    StratuxState,
    TrafficTarget,
)


class FakePainter:
    def __init__(self):
        self.polygons = []
        self.text = []

    def save(self):
        pass

    def restore(self):
        pass

    def setFont(self, *args):
        pass

    def setPen(self, *args):
        pass

    def setBrush(self, *args):
        pass

    def drawPolygon(self, polygon):
        self.polygons.append(
            polygon
        )

    def drawText(self, *args):
        self.text.append(
            args[-1]
        )


def test_traffic_overlay_draws_valid_targets(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    # Populate the initial FlightData object just as
    # the normal application timer would.
    widget.update_data()

    widget.pfd.latitude_deg = 39.363833
    widget.pfd.longitude_deg = -84.522000
    widget.pfd.position_valid = True
    widget.pfd.pressure_alt_ft = 1500.0

    widget.sensor_watchdog_state = (
        widget.sensor_watchdog.evaluate(
            flight_data_available=True,
            position_valid=True,
            position_fresh=True,
            attitude_valid=True,
            attitude_fresh=True,
            air_data_valid=True,
            air_data_fresh=True,
        )
    )

    state = StratuxState(
        ok=True,
        traffic=[
            TrafficTarget(
                callsign="NTEST1",
                latitude_deg=39.397166,
                longitude_deg=-84.522000,
                pressure_alt_ft=2000.0,
                vertical_speed_fpm=600.0,
                traffic_alert=False,
                position_valid=True,
            ),
            TrafficTarget(
                callsign="ALERT1",
                latitude_deg=39.363833,
                longitude_deg=-84.478900,
                pressure_alt_ft=1200.0,
                vertical_speed_fpm=-700.0,
                traffic_alert=True,
                position_valid=True,
            ),
        ],
    )

    painter = FakePainter()

    widget.draw_traffic_overlay(
        painter,
        state,
        1024,
        600,
    )

    assert len(
        painter.polygons
    ) == 2

    assert "TFC ON" in painter.text
    assert "+05↑" in painter.text
    assert "-03↓" in painter.text
    assert "ALERT1" in painter.text


def test_traffic_overlay_fails_closed_on_stale_position(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    # Populate the initial FlightData object just as
    # the normal application timer would.
    widget.update_data()

    widget.pfd.latitude_deg = 39.363833
    widget.pfd.longitude_deg = -84.522000
    widget.pfd.position_valid = True
    widget.pfd.pressure_alt_ft = 1500.0

    widget.sensor_watchdog_state = (
        widget.sensor_watchdog.evaluate(
            flight_data_available=True,
            position_valid=True,
            position_fresh=False,
            attitude_valid=True,
            attitude_fresh=True,
            air_data_valid=True,
            air_data_fresh=True,
        )
    )

    state = StratuxState(
        ok=True,
        traffic=[
            TrafficTarget(
                callsign="STALE",
                latitude_deg=39.397166,
                longitude_deg=-84.522000,
                pressure_alt_ft=2000.0,
                position_valid=True,
            ),
        ],
    )

    painter = FakePainter()

    widget.draw_traffic_overlay(
        painter,
        state,
        1024,
        600,
    )

    assert painter.polygons == []
    assert "TFC ON" in painter.text
