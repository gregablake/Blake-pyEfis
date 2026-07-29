from pyefis.user.blake_pfd.core.landing_site_monitor import (
    LandingSiteMonitor,
)


def test_selected_airport_within_glide():
    monitor = LandingSiteMonitor()

    result = monitor.evaluate(
        selected_airport_distance_nm=5.0,
        max_glide_distance_nm=10.0,
    )

    assert result.airport_reachable is True


def test_selected_airport_outside_glide():
    monitor = LandingSiteMonitor()

    result = monitor.evaluate(
        selected_airport_distance_nm=12.0,
        max_glide_distance_nm=8.0,
    )

    assert result.airport_reachable is False
    assert (
        result.warning
        == "AIRPORT_OUT_OF_GLIDE_RANGE"
    )