from types import SimpleNamespace

from pyefis.user.blake_pfd.core.page_renderer import PageRenderer


class DummyPageManager:
    def __init__(self, page: str) -> None:
        self._page = page

    def current(self) -> str:
        return self._page


def test_page_renderer_draw_page_uses_page_specific_drawer() -> None:
    calls: list[tuple[str, tuple[object, ...]]] = []

    app = SimpleNamespace(
        page_manager=DummyPageManager("FMS"),
        pfd=object(),
        route_manager=object(),
        width=lambda: 1000,
        height=lambda: 800,
        config=SimpleNamespace(navigation=SimpleNamespace(selected_waypoint_id="KJFK")),
        database=object(),
        fms_page=SimpleNamespace(draw=lambda *args, **kwargs: calls.append(("fms", args))),
        airport_info_page=SimpleNamespace(draw=lambda *args, **kwargs: None),
        nearest_page=SimpleNamespace(draw=lambda *args, **kwargs: None),
        ems_page=SimpleNamespace(draw=lambda *args, **kwargs: None),
        ems_trend_page=SimpleNamespace(draw=lambda *args, **kwargs: None),
        ems_alert_history=SimpleNamespace(draw=lambda *args, **kwargs: None),
        engine_checklist_page=SimpleNamespace(draw=lambda *args, **kwargs: None),
        warning_manager=SimpleNamespace(draw=lambda *args, **kwargs: None),
        draw_touch_navigation=lambda *args, **kwargs: None,
    )

    renderer = PageRenderer(app)
    painter = object()

    assert renderer.draw_page(painter) is True
    assert calls == [("fms", (painter, app.route_manager, app.pfd, 1000, 800))]
