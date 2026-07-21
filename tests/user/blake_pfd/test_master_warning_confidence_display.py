from types import SimpleNamespace

from pyefis.user.blake_pfd import master_warning


class FakePainter:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def setFont(self, *args) -> None:
        pass

    def fillRect(self, *args) -> None:
        pass

    def setPen(self, *args) -> None:
        pass

    def drawText(self, *args) -> None:
        if args and isinstance(args[-1], str):
            self.texts.append(args[-1])


def test_master_warning_displays_ai_urgency_and_confidence(
    monkeypatch,
) -> None:
    painter = FakePainter()

    monkeypatch.setattr(
        master_warning,
        "get_engine_warnings",
        lambda engine: [],
    )

    monkeypatch.setattr(
        master_warning,
        "get_checklist_warnings",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        master_warning,
        "load_config",
        lambda: SimpleNamespace(
            ems_test=SimpleNamespace(
                mode="normal",
            )
        ),
    )

    recommendation = SimpleNamespace(
        severity="CAUTION",
        title="CHT Cooling Advisor",
        urgency_s=25.0,
        confidence=0.85,
    )

    master_warning.draw_master_warning_strip(
        painter=painter,
        engine=SimpleNamespace(),
        width=1000,
        checklist=None,
        aircraft_moving=True,
        aircraft_recommendation=recommendation,
    )

    assert any(
        "AI CHT COOLING ADVISOR 25s 85%" in text
        for text in painter.texts
    )


def test_master_warning_omits_missing_confidence(
    monkeypatch,
) -> None:
    painter = FakePainter()

    monkeypatch.setattr(
        master_warning,
        "get_engine_warnings",
        lambda engine: [],
    )

    monkeypatch.setattr(
        master_warning,
        "get_checklist_warnings",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        master_warning,
        "load_config",
        lambda: SimpleNamespace(
            ems_test=SimpleNamespace(
                mode="normal",
            )
        ),
    )

    recommendation = SimpleNamespace(
        severity="CAUTION",
        title="Engine Trend",
        urgency_s=40.0,
        confidence=None,
    )

    master_warning.draw_master_warning_strip(
        painter=painter,
        engine=SimpleNamespace(),
        width=1000,
        checklist=None,
        aircraft_moving=True,
        aircraft_recommendation=recommendation,
    )

    assert any(
        text == "AI ENGINE TREND 40s"
        for text in painter.texts
    )