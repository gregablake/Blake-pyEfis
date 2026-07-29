from pyefis.user.blake_pfd.core.landing_site_monitor import (
    LandingSiteMonitor,
)


def test_airport_within_glide():
    monitor = LandingSiteMonitor()

    result = monitor.evaluate(
        selected_airport_distance_nm=8.0,
        max_glide_distance_nm=10.0,
    )

    assert result.airport_reachable is True
    assert result.warning == ""


def test_airport_out_of_glide():
    monitor = LandingSiteMonitor()

    result = monitor.evaluate(
        selected_airport_distance_nm=15.0,
        max_glide_distance_nm=10.0,
    )

    assert result.airport_reachable is False
    assert result.warning == "AIRPORT_OUT_OF_GLIDE_RANGE"


def test_no_airport_selected():
    monitor = LandingSiteMonitor()

    result = monitor.evaluate(
        selected_airport_distance_nm=None,
        max_glide_distance_nm=10.0,
    )

    assert result.airport_reachable is False
    assert result.warning == "NO_AIRPORT_SELECTED"