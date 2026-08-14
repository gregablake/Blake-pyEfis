from __future__ import annotations

import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PyQt6.QtWidgets import QApplication

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


def test_pfd_demo_constructs() -> None:
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

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
        widget.close()