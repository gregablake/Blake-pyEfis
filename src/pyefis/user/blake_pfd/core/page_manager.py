from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    name: str
    hotkey: str


class PageManager:
    def __init__(self) -> None:
        self.pages: dict[str, Page] = {}
        self.current_page: str = "PFD"

    def register(self, name: str, hotkey: str) -> None:
        self.pages[name] = Page(name=name, hotkey=hotkey.upper())

    def set_page(self, name: str) -> None:
        if name in self.pages:
            self.current_page = name

    def current(self) -> str:
        return self.current_page

    def from_hotkey(self, key: str) -> str | None:
        key = key.upper()

        for page in self.pages.values():
            if page.hotkey == key:
                return page.name

        return None

    def all_pages(self) -> list[Page]:
        return list(self.pages.values())