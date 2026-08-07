from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite


@dataclass(frozen=True)
class TouchRect:
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
class GuidanceTouchSettings:
    hits_enabled: bool = True
    flight_director_enabled: bool = True
    flight_path_marker_enabled: bool = True
    synthetic_vision_enabled: bool = True


@dataclass(frozen=True)
class GuidanceTouchButton:
    key: str
    label: str
    bounds: TouchRect
    enabled: bool


@dataclass(frozen=True)
class GuidanceTouchMenuState:
    visible: bool = False
    settings: GuidanceTouchSettings = (
        GuidanceTouchSettings()
    )
    buttons: tuple[
        GuidanceTouchButton,
        ...,
    ] = ()


class TouchGuidanceMenu:
    BUTTON_DEFINITIONS = (
        (
            "hits_enabled",
            "HITS BOXES",
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
        panel_width: float = 360.0,
        button_height: float = 64.0,
        button_spacing: float = 10.0,
        panel_margin: float = 20.0,
    ) -> None:
        self.panel_width = self._require_positive(
            panel_width,
            "panel_width",
        )

        self.button_height = self._require_positive(
            button_height,
            "button_height",
        )

        self.button_spacing = (
            self._require_nonnegative(
                button_spacing,
                "button_spacing",
            )
        )

        self.panel_margin = (
            self._require_nonnegative(
                panel_margin,
                "panel_margin",
            )
        )

        self.state = GuidanceTouchMenuState()

    def open(
        self,
        *,
        screen_width,
        screen_height,
        settings: GuidanceTouchSettings,
    ) -> GuidanceTouchMenuState:
        width = self._safe_positive(
            screen_width
        )
        height = self._safe_positive(
            screen_height
        )

        if width is None or height is None:
            self.state = GuidanceTouchMenuState(
                visible=False,
                settings=settings,
            )
            return self.state

        buttons = self._build_buttons(
            screen_width=width,
            screen_height=height,
            settings=settings,
        )

        self.state = GuidanceTouchMenuState(
            visible=True,
            settings=settings,
            buttons=buttons,
        )

        return self.state

    def close(self) -> GuidanceTouchMenuState:
        self.state = GuidanceTouchMenuState(
            visible=False,
            settings=self.state.settings,
        )

        return self.state

    def toggle_visibility(
        self,
        *,
        screen_width,
        screen_height,
        settings: GuidanceTouchSettings,
    ) -> GuidanceTouchMenuState:
        if self.state.visible:
            return self.close()

        return self.open(
            screen_width=screen_width,
            screen_height=screen_height,
            settings=settings,
        )

    def handle_touch(
        self,
        *,
        point_x,
        point_y,
    ) -> GuidanceTouchMenuState:
        if not self.state.visible:
            return self.state

        x = self._safe_number(
            point_x
        )
        y = self._safe_number(
            point_y
        )

        if x is None or y is None:
            return self.state

        selected_key = None

        for button in self.state.buttons:
            if button.bounds.contains(
                x,
                y,
            ):
                selected_key = button.key
                break

        if selected_key is None:
            return self.state

        current_value = bool(
            getattr(
                self.state.settings,
                selected_key,
            )
        )

        updated_settings = replace(
            self.state.settings,
            **{
                selected_key: not current_value,
            },
        )

        updated_buttons = tuple(
            replace(
                button,
                enabled=bool(
                    getattr(
                        updated_settings,
                        button.key,
                    )
                ),
            )
            for button in self.state.buttons
        )

        self.state = GuidanceTouchMenuState(
            visible=True,
            settings=updated_settings,
            buttons=updated_buttons,
        )

        return self.state

    def _build_buttons(
        self,
        *,
        screen_width: float,
        screen_height: float,
        settings: GuidanceTouchSettings,
    ) -> tuple[
        GuidanceTouchButton,
        ...,
    ]:
        panel_width = min(
            self.panel_width,
            max(
                1.0,
                screen_width
                - self.panel_margin * 2.0,
            ),
        )

        total_height = (
            len(
                self.BUTTON_DEFINITIONS
            )
            * self.button_height
            + (
                len(
                    self.BUTTON_DEFINITIONS
                )
                - 1
            )
            * self.button_spacing
        )

        start_x = max(
            self.panel_margin,
            screen_width
            - panel_width
            - self.panel_margin,
        )

        start_y = max(
            self.panel_margin,
            (
                screen_height
                - total_height
            )
            / 2.0,
        )

        buttons: list[
            GuidanceTouchButton
        ] = []

        for index, (
            key,
            label,
        ) in enumerate(
            self.BUTTON_DEFINITIONS
        ):
            button_y = (
                start_y
                + index
                * (
                    self.button_height
                    + self.button_spacing
                )
            )

            buttons.append(
                GuidanceTouchButton(
                    key=key,
                    label=label,
                    bounds=TouchRect(
                        x=start_x,
                        y=button_y,
                        width=panel_width,
                        height=self.button_height,
                    ),
                    enabled=bool(
                        getattr(
                            settings,
                            key,
                        )
                    ),
                )
            )

        return tuple(buttons)

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