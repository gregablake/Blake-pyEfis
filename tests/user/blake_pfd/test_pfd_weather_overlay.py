from types import SimpleNamespace

from pyefis.user.blake_pfd.core.fisb_nexrad import (
    NexradBlock,
)
from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)
from pyefis.user.blake_pfd.weather_reader import (
    WeatherState,
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

    def setClipRect(self, *args):
        pass

    def drawPolygon(
        self,
        polygon,
    ):
        self.polygons.append(
            polygon
        )

    def drawText(
        self,
        *args,
    ):
        self.text.append(
            args[-1]
        )


def _weather_block():
    intensity = [
        0
    ] * 128

    # One visible level-4 cell near ownship.
    intensity[0] = 4

    return NexradBlock(
        product_id=63,
        scale_factor=0,
        lat_north_deg=39.38,
        lon_west_deg=-84.54,
        height_deg=(
            4.0 / 60.0
        ),
        width_deg=(
            48.0 / 60.0
        ),
        intensity=tuple(
            intensity
        ),
    )


def _prepare_widget(
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
    qtbot.addWidget(
        widget
    )

    widget.update_data()

    widget.pfd.latitude_deg = (
        39.363833
    )

    widget.pfd.longitude_deg = (
        -84.522000
    )

    widget.pfd.position_valid = True

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

    return widget


def test_weather_overlay_draws_fresh_nexrad(
    qtbot,
    tmp_path,
):
    widget = _prepare_widget(
        qtbot,
        tmp_path,
    )

    painter = FakePainter()

    state = WeatherState(
        ok=True,
        nexrad_blocks=[
            _weather_block()
        ],
        last_update_s=100.0,
    )

    widget.draw_weather_overlay(
        painter,
        state,
        1024,
        600,
    )

    assert (
        "WX ON"
        in painter.text
    )

    assert len(
        painter.polygons
    ) == 1


def test_weather_overlay_fails_closed_on_stale_position(
    qtbot,
    tmp_path,
):
    widget = _prepare_widget(
        qtbot,
        tmp_path,
    )

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

    painter = FakePainter()

    state = WeatherState(
        ok=True,
        nexrad_blocks=[
            _weather_block()
        ],
        last_update_s=100.0,
    )

    widget.draw_weather_overlay(
        painter,
        state,
        1024,
        600,
    )

    assert (
        "WX POS"
        in painter.text
    )

    assert (
        painter.polygons
        == []
    )
