from pyefis.user.blake_pfd.core.direct_to import (
    DirectToManager,
)


def test_direct_to_updates_as_aircraft_moves() -> None:
    manager = DirectToManager()

    initial = manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    updated = manager.update(
        aircraft_lat_deg=39.2000,
        aircraft_lon_deg=-84.5150,
    )

    assert initial.active is True
    assert updated.active is True
    assert updated.identifier == "KHAO"

    assert initial.distance_nm is not None
    assert updated.distance_nm is not None

    assert (
        updated.distance_nm
        < initial.distance_nm
    )


def test_direct_to_can_be_replaced() -> None:
    manager = DirectToManager()

    manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

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


def test_clear_ends_direct_to() -> None:
    manager = DirectToManager()

    manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    state = manager.clear()

    assert state.active is False