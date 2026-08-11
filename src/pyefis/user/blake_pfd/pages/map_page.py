from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen


class MapPage:
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
                10,
                15,
                20,
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
                40,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "MOVING MAP",
        )

        if app.pfd is None:
            return

        painter.save()

        painter.translate(
            app.map_viewport_state.offset_x_px,
            app.map_viewport_state.offset_y_px,
        )

        app.draw_moving_map(
            painter,
            app.pfd,
            width,
            height,
        )

        painter.restore()

        if not app.map_viewport_state.centered:
            painter.setPen(
                QPen(
                    QColor(
                        255,
                        191,
                        0,
                    ),
                    2,
                )
            )

            font = painter.font()
            font.setBold(True)
            font.setPointSize(12)
            painter.setFont(font)

            painter.drawText(
                QRectF(
                    20,
                    60,
                    220,
                    30,
                ),
                Qt.AlignmentFlag.AlignLeft,
                "MAP PAN — TAP CTR",
            )

        app.draw_map_airport_selection(
            painter,
            width,
            height,
        )

        app.draw_touch_map_controls(
            painter,
            width,
            height,
        )