from types import SimpleNamespace

from pyefis.user.blake_pfd.ems_page import EmsPage


class FakePainter:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def fillRect(self, *args) -> None:
        pass

    def setPen(self, *args) -> None:
        pass

    def drawRect(self, *args) -> None:
        pass

    def setFont(self, *args) -> None:
        pass

    def drawText(self, *args) -> None:
        if args and isinstance(args[-1], str):
            self.texts.append(args[-1])


def test_engine_advice_box_displays_pilot_guidance() -> None:
    page = object.__new__(EmsPage)
    painter = FakePainter()

    advice = SimpleNamespace(
        severity="CAUTION",
        title="CHT Cooling Advisor",
        reason="Cooling airflow insufficient during climb.",
        action="Increase airspeed and reduce climb angle.",
        confidence=0.85,
    )

    page.draw_engine_advice_box(
        painter=painter,
        advice=advice,
        width=1000,
        height=700,
    )

    assert any(
        "ENGINE ADVISOR: CHT Cooling Advisor" in text
        for text in painter.texts
    )

    assert any(
        "CONF 85%" in text
        for text in painter.texts
    )

    assert any(
        "WHY: Cooling airflow insufficient" in text
        for text in painter.texts
    )

    assert any(
        "ACTION: Increase airspeed" in text
        for text in painter.texts
    )


def test_normal_engine_advice_box_draws_nothing() -> None:
    page = object.__new__(EmsPage)
    painter = FakePainter()

    advice = SimpleNamespace(
        severity="NORMAL",
        title="Engine Normal",
        reason="No abnormal condition.",
        action="Continue normal operation.",
        confidence=1.0,
    )

    page.draw_engine_advice_box(
        painter=painter,
        advice=advice,
        width=1000,
        height=700,
    )

    assert painter.texts == []