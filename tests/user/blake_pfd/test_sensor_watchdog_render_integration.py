from pathlib import Path

from PyQt6.QtGui import QImage, QPainter

from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


def test_stale_gps_banner_appears_and_clears_in_full_render(
    qtbot,
    tmp_path: Path,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=tmp_path / "baro.json",
    )

    widget.timer.stop()
    qtbot.addWidget(widget)
    widget.resize(1024, 600)
    widget.update_data()

    assert widget.pfd is not None

    widget.config.features.show_traffic = False
    widget.config.features.show_weather = False

    def set_gps_freshness(fresh: bool) -> None:
        widget.sensor_watchdog_state = (
            widget.sensor_watchdog.evaluate(
                flight_data_available=True,
                position_valid=True,
                position_fresh=fresh,
                attitude_valid=True,
                attitude_fresh=True,
                air_data_valid=True,
                air_data_fresh=True,
            )
        )

    def render_image() -> QImage:
        image = QImage(
            1024,
            600,
            QImage.Format.Format_ARGB32,
        )
        image.fill(0)

        painter = QPainter(image)

        try:
            widget.render(painter)
        finally:
            painter.end()

        assert image.isNull() is False
        return image

    # Sample inside the watchdog banner's background,
    # away from its centered warning text.
    sample_x = 342
    sample_y = 100

    # 1. Fresh GPS: no sensor-degradation banner.
    set_gps_freshness(True)

    assert widget.sensor_watchdog_state.degraded is False

    healthy_image = render_image()
    healthy_pixel = healthy_image.pixelColor(
        sample_x,
        sample_y,
    )

    # 2. Stale GPS: a degradation warning must appear.
    set_gps_freshness(False)

    assert widget.sensor_watchdog_state.degraded is True
    assert (
        widget.sensor_watchdog_state.message
        == "DEGRADED: GPS STALE"
    )

    stale_image = render_image()
    stale_pixel = stale_image.pixelColor(
        sample_x,
        sample_y,
    )

    assert stale_pixel != healthy_pixel

    # The production degraded-state banner has an
    # amber background; verify the rendered pixel.
    assert stale_pixel.red() >= 140
    assert stale_pixel.green() >= 75
    assert stale_pixel.blue() <= 65

    # 3. GPS recovers: the warning must disappear,
    # restoring the original background pixel.
    set_gps_freshness(True)

    assert widget.sensor_watchdog_state.degraded is False

    recovered_image = render_image()
    recovered_pixel = recovered_image.pixelColor(
        sample_x,
        sample_y,
    )

    assert recovered_pixel == healthy_pixel

    widget.close()
