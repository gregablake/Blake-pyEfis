from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutRect:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


@dataclass(frozen=True)
class PfdLayout:
    """
    Central geometry authority for the Blake PFD.

    Baseline design target:
        1024 x 600

    Layout philosophy:
        - compact EMS column on the left
        - protected primary-flight / synthetic-vision
          viewport in the center
        - navigation / flight-plan column on the right
        - thin status bars at top and bottom
    """

    screen: LayoutRect
    top_bar: LayoutRect
    left_panel: LayoutRect
    flight_view: LayoutRect
    right_panel: LayoutRect
    bottom_bar: LayoutRect

    @classmethod
    def build(
        cls,
        width: int,
        height: int,
    ) -> "PfdLayout":
        if width <= 0 or height <= 0:
            raise ValueError(
                "PFD dimensions must be positive"
            )

        # Scale from the intended 1024 x 600 panel.
        top_h = round(
            height
            * 36
            / 600
        )

        bottom_h = round(
            height
            * 30
            / 600
        )

        left_w = round(
            width
            * 180
            / 1024
        )

        right_w = round(
            width
            * 200
            / 1024
        )

        main_y = top_h

        main_h = (
            height
            - top_h
            - bottom_h
        )

        flight_x = left_w

        flight_w = (
            width
            - left_w
            - right_w
        )

        return cls(
            screen=LayoutRect(
                x=0,
                y=0,
                width=width,
                height=height,
            ),
            top_bar=LayoutRect(
                x=0,
                y=0,
                width=width,
                height=top_h,
            ),
            left_panel=LayoutRect(
                x=0,
                y=main_y,
                width=left_w,
                height=main_h,
            ),
            flight_view=LayoutRect(
                x=flight_x,
                y=main_y,
                width=flight_w,
                height=main_h,
            ),
            right_panel=LayoutRect(
                x=flight_x + flight_w,
                y=main_y,
                width=right_w,
                height=main_h,
            ),
            bottom_bar=LayoutRect(
                x=0,
                y=height - bottom_h,
                width=width,
                height=bottom_h,
            ),
        )
