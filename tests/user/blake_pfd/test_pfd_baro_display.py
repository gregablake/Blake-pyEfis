from types import SimpleNamespace

from pyefis.user.blake_pfd.core.baro_setting_controller import (
    BaroSettingController,
)
from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


class RecordingPainter:
    def __init__(self):
        self.text = []

    def fillRect(
        self,
        *args,
    ):
        pass

    def setPen(
        self,
        *args,
    ):
        pass

    def drawRect(
        self,
        *args,
    ):
        pass

    def setFont(
        self,
        *args,
    ):
        pass

    def drawLine(
        self,
        *args,
    ):
        pass

    def drawText(
        self,
        *args,
    ):
        self.text.append(
            str(args[-1])
        )


def make_app(
    setting_inhg=29.92,
):
    controller = BaroSettingController(
        initial_inhg=setting_inhg,
    )

    return SimpleNamespace(
        flight_computer=SimpleNamespace(
            baro_setting_controller=controller,
        )
    )


def make_pfd():
    return SimpleNamespace(
        indicated_alt_ft=1500.0,
    )


def test_altitude_tape_draws_current_baro_setting():
    painter = RecordingPainter()
    app = make_app(
        29.92
    )

    BlakePfdDemo.draw_altitude_tape(
        app,
        painter,
        make_pfd(),
        1024,
        600,
    )

    rendered = " ".join(
        painter.text
    )

    assert "BARO" in rendered
    assert "29.92" in rendered


def test_altitude_tape_draws_updated_runtime_baro():
    painter = RecordingPainter()
    app = make_app(
        29.92
    )

    assert (
        app.flight_computer
        .baro_setting_controller
        .set_setting(30.17)
        is True
    )

    BlakePfdDemo.draw_altitude_tape(
        app,
        painter,
        make_pfd(),
        1024,
        600,
    )

    rendered = " ".join(
        painter.text
    )

    assert "30.17" in rendered
    assert "29.92" not in rendered
