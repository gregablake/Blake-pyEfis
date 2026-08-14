from __future__ import annotations

import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


def test_pfd_demo_constructs(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    try:
        assert widget is not None
        assert widget.config is not None
        assert widget.page_manager is not None
        assert widget.direct_to_guidance is not None
        assert (
            widget.direct_to_lateral_guidance
            is not None
        )
    finally:
        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()


def test_pfd_demo_renders_offscreen(
    qapp: QApplication,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
    )

    widget.resize(
        1280,
        720,
    )

    image = QImage(
        1280,
        720,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.update_data()

        widget.render(
            painter,
        )

        assert image.isNull() is False
    finally:
        painter.end()

        if widget.timer.isActive():
            widget.timer.stop()

        widget.close()
        widget.deleteLater()
        qapp.processEvents()