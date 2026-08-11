from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class MapTouchRect:
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
class MapTouchButton:
    key: str
    label: str
    bounds: MapTouchRect


@dataclass(frozen=True)
class TouchMapState:
    buttons: tuple[
        MapTouchButton,
        ...,
    ] = ()


class TouchMapControls:
    BUTTON_DEFINITIONS = (
        (
            "zoom_in",
            "+",
        ),
        (
            "zoom_out",
            "-",
        ),
        (
            "center",
            "CTR",
        ),
        (
            "orientation",
            "N/TRK",
        ),
    )

    def __init__(
        self,
        *,
        button_width: float = 72.0,
        button_height: float = 64.0,
        spacing: float = 10.0,
        right_margin: float = 18.0,
        top_margin: float = 90.0,
    ) -> None:
        self.button_width = self._require_positive(
            button_width,
            "button_width",
        )

        self.button_height = self._require_positive(
            button_height,
            "button_height",
        )

        self.spacing = self._require_nonnegative(
            spacing,
            "spacing",
        )

        self.right_margin = self._require_nonnegative(
            right_margin,
            "right_margin",
        )

        self.top_margin = self._require_nonnegative(
            top_margin,
            "top_margin",
        )

        self.state = TouchMapState()

    def layout(
        self,
        *,
        screen_width,
        screen_height,
    ) -> TouchMapState:
        width = self._safe_positive(
            screen_width
        )

        height = self._safe_positive(
            screen_height
        )

        if width is None or height is None:
            self.state = TouchMapState()
            return self.state

        button_x = (
            width
            - self.button_width
            - self.right_margin
        )

        buttons: list[
            MapTouchButton
        ] = []

        for index, (
            key,
            label,
        ) in enumerate(
            self.BUTTON_DEFINITIONS
        ):
            button_y = (
                self.top_margin
                + index
                * (
                    self.button_height
                    + self.spacing
                )
            )

            if (
                button_y
                + self.button_height
                > height
            ):
                break

            buttons.append(
                MapTouchButton(
                    key=key,
                    label=label,
                    bounds=MapTouchRect(
                        x=button_x,
                        y=button_y,
                        width=self.button_width,
                        height=self.button_height,
                    ),
                )
            )

        self.state = TouchMapState(
            buttons=tuple(
                buttons
            ),
        )

        return self.state

    def action_for_touch(
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
                return button.key

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