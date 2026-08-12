from pyefis.user.blake_pfd.core.direct_to import (
    DirectToManager,
)


def test_direct_to_starts_inactive() -> None:
    manager = DirectToManager()

    assert manager.state.active is False
    assert manager.state.identifier is None


def test_activate_direct_to() -> None:
    manager = DirectToManager()

    state = manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    assert state.active is True
    assert state.identifier == "KHAO"
    assert state.name == "Butler County Regional"
    assert state.distance_nm is not None
    assert state.distance_nm > 0.0
    assert state.bearing_deg is not None


def test_identifier_is_uppercase() -> None:
    manager = DirectToManager()

    state = manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="khao",
        target_name="Test",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    assert state.identifier == "KHAO"


def test_update_recalculates_distance() -> None:
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

    assert updated.active is True
    assert updated.distance_nm is not None
    assert initial.distance_nm is not None
    assert updated.distance_nm < initial.distance_nm


def test_update_preserves_target() -> None:
    manager = DirectToManager()

    manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    updated = manager.update(
        aircraft_lat_deg=39.1500,
        aircraft_lon_deg=-84.5150,
    )

    assert updated.identifier == "KHAO"
    assert (
        updated.target_lat_deg
        == 39.3638
    )
    assert (
        updated.target_lon_deg
        == -84.5220
    )


def test_clear_direct_to() -> None:
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
    assert state.identifier is None


def test_invalid_position_does_not_activate() -> None:
    manager = DirectToManager()

    state = manager.activate(
        aircraft_lat_deg="bad",
        aircraft_lon_deg=-84.5120,
        target_identifier="KHAO",
        target_name="Butler County Regional",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    assert state.active is False


def test_empty_identifier_does_not_activate() -> None:
    manager = DirectToManager()

    state = manager.activate(
        aircraft_lat_deg=39.1031,
        aircraft_lon_deg=-84.5120,
        target_identifier="",
        target_name="",
        target_lat_deg=39.3638,
        target_lon_deg=-84.5220,
    )

    assert state.active is False