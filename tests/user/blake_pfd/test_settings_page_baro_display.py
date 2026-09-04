from types import SimpleNamespace

from pyefis.user.blake_pfd.core.baro_setting_controller import (
    BaroSettingController,
)
from pyefis.user.blake_pfd.core.touch_baro_setting import (
    TouchBaroSetting,
)
from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
)
from pyefis.user.blake_pfd.core.touch_settings import (
    TouchSettings,
)
from pyefis.user.blake_pfd.pages.settings_page import (
    SettingsPage,
)


class DummyFont:
    def setBold(
        self,
        value,
    ):
        pass

    def setPointSize(
        self,
        value,
    ):
        pass


class RecordingPainter:
    def __init__(self):
        self.text = []
        self._font = DummyFont()

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

    def setBrush(
        self,
        *args,
    ):
        pass

    def setFont(
        self,
        *args,
    ):
        pass

    def font(
        self,
    ):
        return self._font

    def drawRoundedRect(
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


def make_app():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    return SimpleNamespace(
        guidance_touch_settings=(
            GuidanceTouchSettings()
        ),
        touch_settings=TouchSettings(),
        touch_settings_state=None,
        touch_baro_setting=TouchBaroSetting(),
        touch_baro_state=None,
        flight_computer=SimpleNamespace(
            baro_setting_controller=controller,
        ),
    )


def test_settings_page_draws_live_baro_setting():
    painter = RecordingPainter()
    app = make_app()

    SettingsPage().draw(
        painter=painter,
        app=app,
        width=1024,
        height=600,
    )

    rendered = " ".join(
        painter.text
    )

    assert "BARO" in rendered
    assert "29.92" in rendered
    assert "IN" in rendered


def test_settings_page_draws_baro_adjustment_symbols():
    painter = RecordingPainter()
    app = make_app()

    SettingsPage().draw(
        painter=painter,
        app=app,
        width=1024,
        height=600,
    )

    assert "-" in painter.text
    assert "+" in painter.text


def test_settings_page_uses_current_runtime_baro_value():
    painter = RecordingPainter()
    app = make_app()

    assert (
        app.flight_computer
        .baro_setting_controller
        .set_setting(30.17)
        is True
    )

    SettingsPage().draw(
        painter=painter,
        app=app,
        width=1024,
        height=600,
    )

    rendered = " ".join(
        painter.text
    )

    assert "30.17" in rendered
    assert "29.92" not in rendered
