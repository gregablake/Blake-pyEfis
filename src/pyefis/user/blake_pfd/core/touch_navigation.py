from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class NavigationTouchRect:
    x: float
    y: float
    width: float
    height: float

    def contains(
        self,
        point_x: float,
        point_y: float,
    ) -> bool:
        return (
            self.x <= point_x <= self.x + self.width
            and self.y <= point_y <= self.y + self.height
        )


@dataclass(frozen=True)
class NavigationTouchButton:
    key: str
    label: str
    page_name: str
    bounds: NavigationTouchRect
    selected: bool = False


@dataclass(frozen=True)
class TouchNavigationState:
    current_page: str = "PFD"
    buttons: tuple[
        NavigationTouchButton,
        ...,
    ] = ()


class TouchNavigation:
    BUTTON_DEFINITIONS = (
        (
            "pfd",
            "PFD",
            "PFD",
        ),
        (
            "map",
            "MAP",
            "MAP",
        ),
        (
            "engine",
            "ENGINE",
            "EMS",
        ),
        (
            "nearest",
            "NEAREST",
            "NEAREST",
        ),
        (
            "settings",
            "SETTINGS",
            "SETTINGS",
        ),
    )

    def __init__(
        self,
        *,
        bar_height: float = 64.0,
        margin: float = 8.0,
        spacing: float = 8.0,
    ) -> None:
        self.bar_height = self._require_positive(
            bar_height,
            "bar_height",
        )

        self.margin = self._require_nonnegative(
            margin,
            "margin",
        )

        self.spacing = self._require_nonnegative(
            spacing,
            "spacing",
        )

        self.state = TouchNavigationState()

    def layout(
        self,
        *,
        screen_width,
        screen_height,
        current_page: str,
    ) -> TouchNavigationState:
        width = self._safe_positive(
            screen_width
        )

        height = self._safe_positive(
            screen_height
        )

        if width is None or height is None:
            self.state = TouchNavigationState(
                current_page=current_page,
            )
            return self.state

        button_count = len(
            self.BUTTON_DEFINITIONS
        )

        available_width = (
            width
            - self.margin * 2.0
            - self.spacing
            * (button_count - 1)
        )

        if available_width <= 0.0:
            self.state = TouchNavigationState(
                current_page=current_page,
            )
            return self.state

        button_width = (
            available_width
            / button_count
        )

        button_y = (
            height
            - self.bar_height
            - self.margin
        )

        buttons: list[
            NavigationTouchButton
        ] = []

        for index, (
            key,
            label,
            page_name,
        ) in enumerate(
            self.BUTTON_DEFINITIONS
        ):
            button_x = (
                self.margin
                + index
                * (
                    button_width
                    + self.spacing
                )
            )

            buttons.append(
                NavigationTouchButton(
                    key=key,
                    label=label,
                    page_name=page_name,
                    bounds=NavigationTouchRect(
                        x=button_x,
                        y=button_y,
                        width=button_width,
                        height=self.bar_height,
                    ),
                    selected=(
                        page_name
                        == current_page
                    ),
                )
            )

        self.state = TouchNavigationState(
            current_page=current_page,
            buttons=tuple(
                buttons
            ),
        )

        return self.state

    def page_for_touch(
        self,
        *,
        point_x,
        point_y,
    ) -> str | None:
        x = self._safe_number(
            point_x
        )

        y = self._safe_number(
            point_y
        )

        if x is None or y is None:
            return None

        for button in self.state.buttons:
            if button.bounds.contains(
                x,
                y,
            ):
                return button.page_name

        return None

    @staticmethod
    def _safe_number(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return number

    @classmethod
    def _safe_positive(
        cls,
        value,
    ) -> float | None:
        number = cls._safe_number(
            value
        )

        if number is None or number <= 0.0:
            return None

        return number

    @classmethod
    def _require_positive(
        cls,
        value,
        name: str,
    ) -> float:
        number = cls._safe_positive(
            value
        )

        if number is None:
            raise ValueError(
                f"{name} must be finite and positive"
            )

        return number

    @classmethod
    def _require_nonnegative(
        cls,
        value,
        name: str,
    ) -> float:
        number = cls._safe_number(
            value
        )

        if number is None or number < 0.0:
            raise ValueError(
                f"{name} must be finite and nonnegative"
            )

        return number