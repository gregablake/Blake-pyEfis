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

        # ----------------------------------------------------
        # Runtime BARO control
        #
        # Use the same geometry object as mousePressEvent()
        # so the visible buttons and active touch regions
        # remain identical.
        # ----------------------------------------------------

        app.touch_baro_state = (
            app.touch_baro_setting.layout(
                screen_width=width,
                screen_height=height,
            )
        )

        if app.touch_baro_state.valid:
            baro_state = app.touch_baro_state

            baro_value = (
                app.flight_computer
                .baro_setting_controller
                .setting_inhg
            )

            font.setPointSize(18)
            font.setBold(True)
            painter.setFont(font)

            # Decrement button
            painter.setBrush(
                QBrush(
                    QColor(
                        55,
                        55,
                        68,
                        245,
                    )
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
                    baro_state.decrement_bounds.x,
                    baro_state.decrement_bounds.y,
                    baro_state.decrement_bounds.width,
                    baro_state.decrement_bounds.height,
                ),
                10.0,
                10.0,
            )

            painter.drawText(
                QRectF(
                    baro_state.decrement_bounds.x,
                    baro_state.decrement_bounds.y,
                    baro_state.decrement_bounds.width,
                    baro_state.decrement_bounds.height,
                ),
                Qt.AlignmentFlag.AlignCenter,
                "-",
            )

            # Current BARO value
            painter.setBrush(
                QBrush(
                    QColor(
                        32,
                        42,
                        58,
                        245,
                    )
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    baro_state.value_bounds.x,
                    baro_state.value_bounds.y,
                    baro_state.value_bounds.width,
                    baro_state.value_bounds.height,
                ),
                10.0,
                10.0,
            )

            painter.drawText(
                QRectF(
                    baro_state.value_bounds.x,
                    baro_state.value_bounds.y,
                    baro_state.value_bounds.width,
                    baro_state.value_bounds.height,
                ),
                Qt.AlignmentFlag.AlignCenter,
                (
                    f"BARO {baro_value:.2f} IN"
                ),
            )

            # Increment button
            painter.setBrush(
                QBrush(
                    QColor(
                        55,
                        55,
                        68,
                        245,
                    )
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    baro_state.increment_bounds.x,
                    baro_state.increment_bounds.y,
                    baro_state.increment_bounds.width,
                    baro_state.increment_bounds.height,
                ),
                10.0,
                10.0,
            )

            painter.drawText(
                QRectF(
                    baro_state.increment_bounds.x,
                    baro_state.increment_bounds.y,
                    baro_state.increment_bounds.width,
                    baro_state.increment_bounds.height,
                ),
                Qt.AlignmentFlag.AlignCenter,
                "+",
            )
