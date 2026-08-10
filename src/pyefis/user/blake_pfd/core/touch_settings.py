from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class SettingsRect:
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
class SettingsButton:
    key: str
    label: str
    bounds: SettingsRect
    enabled: bool


@dataclass(frozen=True)
class TouchSettingsState:
    buttons: tuple[
        SettingsButton,
        ...,
    ] = ()


class TouchSettings:
    BUTTON_DEFINITIONS = (
        (
            "hits_enabled",
            "HITS",
        ),
        (
            "flight_director_enabled",
            "FLIGHT DIRECTOR",
        ),
        (
            "flight_path_marker_enabled",
            "FLIGHT PATH MARKER",
        ),
        (
            "synthetic_vision_enabled",
            "SYNTHETIC VISION",
        ),
    )

    def __init__(
        self,
        *,
        side_margin: float = 60.0,
        top_margin: float = 90.0,
        bottom_reserved: float = 90.0,
        button_height: float = 72.0,
        spacing: float = 16.0,
    ) -> None:
        self.side_margin = self._require_nonnegative(
            side_margin,
            "side_margin",
        )

        self.top_margin = self._require_nonnegative(
            top_margin,
            "top_margin",
        )

        self.bottom_reserved = self._require_nonnegative(
            bottom_reserved,
            "bottom_reserved",
        )

        self.button_height = self._require_positive(
            button_height,
            "button_height",
        )

        self.spacing = self._require_nonnegative(
            spacing,
            "spacing",
        )

        self.state = TouchSettingsState()

    def layout(
        self,
        *,
        screen_width,
        screen_height,
        values,
    ) -> TouchSettingsState:
        width = self._safe_positive(
            screen_width
        )

        height = self._safe_positive(
            screen_height
        )

        if width is None or height is None:
            self.state = TouchSettingsState()
            return self.state

        available_width = (
            width
            - self.side_margin * 2.0
        )

        if available_width <= 0.0:
            self.state = TouchSettingsState()
            return self.state

        maximum_y = (
            height
            - self.bottom_reserved
        )

        buttons: list[
            SettingsButton
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
                > maximum_y
            ):
                break

            buttons.append(
                SettingsButton(
                    key=key,
                    label=label,
                    bounds=SettingsRect(
                        x=self.side_margin,
                        y=button_y,
                        width=available_width,
                        height=self.button_height,
                    ),
                    enabled=bool(
                        getattr(
                            values,
                            key,
                        )
                    ),
                )
            )

        self.state = TouchSettingsState(
            buttons=tuple(
                buttons
            ),
        )

        return self.state

    def key_for_touch(
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