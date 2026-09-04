from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class BaroTouchRect:
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    def contains(
        self,
        point_x: float,
        point_y: float,
    ) -> bool:
        return (
            self.x
            <= point_x
            <= self.x + self.width
            and self.y
            <= point_y
            <= self.y + self.height
        )


@dataclass(frozen=True)
class TouchBaroState:
    valid: bool = False
    decrement_bounds: BaroTouchRect = BaroTouchRect()
    value_bounds: BaroTouchRect = BaroTouchRect()
    increment_bounds: BaroTouchRect = BaroTouchRect()


class TouchBaroSetting:
    """
    Touch geometry for the pilot BARO control.

    Layout:
        [   -   ] [  BARO VALUE  ] [   +   ]

    Only the minus and plus regions return actions.
    The value region is display-only.
    """

    def __init__(
        self,
        *,
        side_margin: float = 60.0,
        row_y: float = 450.0,
        button_height: float = 72.0,
        spacing: float = 16.0,
        adjustment_width: float = 180.0,
    ) -> None:
        self.side_margin = self._require_nonnegative(
            side_margin,
            "side_margin",
        )

        self.row_y = self._require_nonnegative(
            row_y,
            "row_y",
        )

        self.button_height = self._require_positive(
            button_height,
            "button_height",
        )

        self.spacing = self._require_nonnegative(
            spacing,
            "spacing",
        )

        self.adjustment_width = self._require_positive(
            adjustment_width,
            "adjustment_width",
        )

        self.state = TouchBaroState()

    def layout(
        self,
        *,
        screen_width,
        screen_height,
    ) -> TouchBaroState:
        width = self._safe_positive(
            screen_width
        )

        height = self._safe_positive(
            screen_height
        )

        if width is None or height is None:
            self.state = TouchBaroState()
            return self.state

        if (
            self.row_y
            + self.button_height
            > height
        ):
            self.state = TouchBaroState()
            return self.state

        usable_width = (
            width
            - 2.0 * self.side_margin
        )

        value_width = (
            usable_width
            - 2.0 * self.adjustment_width
            - 2.0 * self.spacing
        )

        if value_width <= 0.0:
            self.state = TouchBaroState()
            return self.state

        decrement_x = self.side_margin

        value_x = (
            decrement_x
            + self.adjustment_width
            + self.spacing
        )

        increment_x = (
            value_x
            + value_width
            + self.spacing
        )

        self.state = TouchBaroState(
            valid=True,
            decrement_bounds=BaroTouchRect(
                x=decrement_x,
                y=self.row_y,
                width=self.adjustment_width,
                height=self.button_height,
            ),
            value_bounds=BaroTouchRect(
                x=value_x,
                y=self.row_y,
                width=value_width,
                height=self.button_height,
            ),
            increment_bounds=BaroTouchRect(
                x=increment_x,
                y=self.row_y,
                width=self.adjustment_width,
                height=self.button_height,
            ),
        )

        return self.state

    def action_for_touch(
        self,
        *,
        point_x,
        point_y,
    ) -> str | None:
        if not self.state.valid:
            return None

        x = self._safe_number(
            point_x
        )

        y = self._safe_number(
            point_y
        )

        if x is None or y is None:
            return None

        if self.state.decrement_bounds.contains(
            x,
            y,
        ):
            return "decrement"

        if self.state.increment_bounds.contains(
            x,
            y,
        ):
            return "increment"

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
