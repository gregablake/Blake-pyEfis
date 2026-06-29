from __future__ import annotations

from time import monotonic

from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.master_warning import get_engine_warnings
from pyefis.user.blake_pfd.gpio_buzzer import GpioBuzzer


class AudioAlertManager:
    def __init__(self, repeat_interval_s: float = 10.0) -> None:
        self.repeat_interval_s = repeat_interval_s
        self.last_alert_time_s = 0.0
        self.last_alert_text: str | None = None
        self.buzzer = GpioBuzzer()

    def update(self, engine: EngineData, silenced: bool = False) -> None:
        if silenced:
            return

        warnings = get_engine_warnings(engine)
        active = [warning.text for warning in warnings if warning.text != "ENGINE NORMAL"]

        if not active:
            self.last_alert_text = None
            return

        alert_text = active[0]
        now_s = monotonic()

        if alert_text != self.last_alert_text or now_s - self.last_alert_time_s >= self.repeat_interval_s:
            self.last_alert_text = alert_text
            self.last_alert_time_s = now_s
            self.play_alert(alert_text)

    def play_alert(self, alert_text: str) -> None:
        print(f"AUDIO ALERT: {alert_text}")
        self.buzzer.beep()