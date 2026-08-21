from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.ems_page import EmsPage


class RecordingPainter:
    def __init__(self) -> None:
        self.text: list[str] = []

    def fillRect(self, *args) -> None:
        pass

    def setPen(self, *args) -> None:
        pass

    def setFont(self, *args) -> None:
        pass

    def drawText(self, *args) -> None:
        if args and isinstance(args[-1], str):
            self.text.append(args[-1])


def test_ems_page_shows_unavailable_without_engine_state() -> None:
    page = EmsPage()
    painter = RecordingPainter()

    aircraft = SimpleNamespace(
        engine_state=None,
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
    )

    assert "ENGINE DATA UNAVAILABLE" in painter.text
    assert "0" not in painter.text

def test_ems_page_shows_stale_fault_message() -> None:
    page = EmsPage()
    painter = RecordingPainter()

    aircraft = SimpleNamespace(
        engine_state=None,
    )

    page.draw(
        painter,
        aircraft,
        width=1024,
        height=600,
        fault_message="EMS DATA STALE",
    )

    assert "EMS DATA STALE" in painter.text
    assert "ENGINE DATA UNAVAILABLE" not in painter.text