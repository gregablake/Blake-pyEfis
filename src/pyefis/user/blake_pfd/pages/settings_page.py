from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QColor,
    QBrush,
    QPainter,
    QPen,
)


class SettingsPage:
    def draw(
        self,
        painter: QPainter,
        app,
        width: int,
        height: int,
    ) -> None:
        painter.fillRect(
            0,
            0,
            width,
            height,
            QColor(
                18,
                18,
                24,
            ),
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    255,
                    255,
                ),
                2,
            )
        )

        font = painter.font()
        font.setBold(True)
        font.setPointSize(20)
        painter.setFont(font)

        painter.drawText(
            QRectF(
                20,
                15,
                width - 40,
                45,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "DISPLAY & GUIDANCE SETTINGS",
        )

        app.touch_settings_state = (
            app.touch_settings.layout(
                screen_width=width,
                screen_height=height,
                values=(
                    app.guidance_touch_settings
                ),
            )
        )

        font.setPointSize(15)
        painter.setFont(font)

        for button in (
            app.touch_settings_state.buttons
        ):
            if button.enabled:
                fill_color = QColor(
                    0,
                    125,
                    80,
                    235,
                )
                state_text = "ON"
            else:
                fill_color = QColor(
                    65,
                    65,
                    75,
                    235,
                )
                state_text = "OFF"

            painter.setBrush(
                QBrush(
                    fill_color
                )
            )

            painter.setPen(
                QPen(
                    QColor(
                        255,
                        255,
                        255,
                    ),
                    2,
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    button.bounds.x,
                    button.bounds.y,
                    button.bounds.width,
                    button.bounds.height,
                ),
                10.0,
                10.0,
            )

            painter.drawText(
                QRectF(
                    button.bounds.x + 22.0,
                    button.bounds.y,
                    button.bounds.width - 130.0,
                    button.bounds.height,
                ),
                Qt.AlignmentFlag.AlignVCenter,
                button.label,
            )

            painter.drawText(
                QRectF(
                    button.bounds.x
                    + button.bounds.width
                    - 100.0,
                    button.bounds.y,
                    70.0,
                    button.bounds.height,
                ),
                (
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignRight
                ),
                state_text,
            )