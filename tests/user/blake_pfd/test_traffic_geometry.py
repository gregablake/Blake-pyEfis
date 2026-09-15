from pyefis.user.blake_pfd.core.traffic_geometry import (
    calculate_traffic_geometry,
)


def test_target_due_north():

    result = calculate_traffic_geometry(
        own_lat_deg=0.0,
        own_lon_deg=0.0,
        own_pressure_alt_ft=1000.0,
        target_lat_deg=0.1,
        target_lon_deg=0.0,
        target_pressure_alt_ft=1500.0,
    )

    assert result is not None

    assert abs(
        result.distance_nm
        - 6.004
    ) < 0.02

    assert abs(
        result.bearing_deg
        - 0.0
    ) < 0.01

    assert (
        result.relative_alt_ft
        == 500.0
    )


def test_target_due_east():

    result = calculate_traffic_geometry(
        own_lat_deg=0.0,
        own_lon_deg=0.0,
        own_pressure_alt_ft=1000.0,
        target_lat_deg=0.0,
        target_lon_deg=0.1,
        target_pressure_alt_ft=800.0,
    )

    assert result is not None

    assert abs(
        result.distance_nm
        - 6.004
    ) < 0.02

    assert abs(
        result.bearing_deg
        - 90.0
    ) < 0.01

    assert (
        result.relative_alt_ft
        == -200.0
    )


def test_missing_altitude_preserves_horizontal_geometry():

    result = calculate_traffic_geometry(
        own_lat_deg=39.0,
        own_lon_deg=-84.0,
        own_pressure_alt_ft=None,
        target_lat_deg=39.05,
        target_lon_deg=-84.0,
        target_pressure_alt_ft=2500.0,
    )

    assert result is not None
    assert result.distance_nm > 0.0

    assert (
        result.relative_alt_ft
        is None
    )


def test_invalid_ownship_position_fails_closed():

    result = calculate_traffic_geometry(
        own_lat_deg=95.0,
        own_lon_deg=-84.0,
        own_pressure_alt_ft=1000.0,
        target_lat_deg=39.0,
        target_lon_deg=-84.0,
        target_pressure_alt_ft=1500.0,
    )

    assert result is None


def test_invalid_target_position_fails_closed():

    result = calculate_traffic_geometry(
        own_lat_deg=39.0,
        own_lon_deg=-84.0,
        own_pressure_alt_ft=1000.0,
        target_lat_deg=39.0,
        target_lon_deg=float("nan"),
        target_pressure_alt_ft=1500.0,
    )

    assert result is None
