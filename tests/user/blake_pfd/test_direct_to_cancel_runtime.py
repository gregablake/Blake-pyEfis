from pyefis.user.blake_pfd.core.direct_to import (
    DirectToManager,
)


def test_cancel_clears_active_direct_to() -> None:
    manager = DirectToManager()

    manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    assert manager.state.active is True

    state = manager.clear()

    assert state.active is False
    assert state.identifier is None
    assert state.distance_nm is None
    assert state.bearing_deg is None


def test_new_direct_to_after_cancel_works() -> None:
    manager = DirectToManager()

    manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    manager.clear()

    state = manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KCVG",
        target_name="Cincinnati Northern Kentucky",
        target_lat_deg=39.0488,
        target_lon_deg=-84.6678,
    )

    assert state.active is True
    assert state.identifier == "KCVG"