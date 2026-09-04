from types import SimpleNamespace

from pyefis.user.blake_pfd.config_loader import (
    SafeTaxiConfig,
)
from pyefis.user.blake_pfd.safe_taxi import (
    SafeTaxiComputer,
)


class FakeAirportDatabase:
    def __init__(
        self,
        *,
        distance_nm=0.2,
        elevation_ft=633.0,
    ):
        self.distance_nm = distance_nm
        self.airport = SimpleNamespace(
            ident="KHAO",
            name="Butler County Regional",
            lat_deg=39.3638,
            lon_deg=-84.5220,
            elevation_ft=elevation_ft,
        )
        self.calls = 0

    def nearest_airports(
        self,
        lat_deg,
        lon_deg,
        max_results=10,
        include_closed=False,
    ):
        self.calls += 1

        return [
            (
                self.distance_nm,
                self.airport,
            )
        ]


def make_flight(
    *,
    gs=10.0,
    ias=10.0,
    altitude=650.0,
    position_valid=True,
):
    return SimpleNamespace(
        ground_speed_kt=gs,
        ias_kt=ias,
        indicated_alt_ft=altitude,
        heading_deg=180.0,
        latitude_deg=39.3638,
        longitude_deg=-84.5220,
        position_valid=position_valid,
    )


def make_computer(
    database=None,
):
    return SafeTaxiComputer(
        database=(
            database
            if database is not None
            else FakeAirportDatabase()
        ),
        config=SafeTaxiConfig(),
    )


def test_valid_airport_surface_conditions_activate():
    computer = make_computer()

    state = computer.update(
        make_flight(),
        position_fresh=True,
        airborne=False,
    )

    assert state.active is True
    assert state.airport_id == "KHAO"
    assert state.airport_name == (
        "Butler County Regional"
    )


def test_invalid_position_fails_closed():
    computer = make_computer()

    state = computer.update(
        make_flight(
            position_valid=False,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert state.active is False


def test_stale_position_fails_closed():
    computer = make_computer()

    state = computer.update(
        make_flight(),
        position_fresh=False,
        airborne=False,
    )

    assert state.active is False


def test_airborne_state_prevents_activation():
    computer = make_computer()

    state = computer.update(
        make_flight(),
        position_fresh=True,
        airborne=True,
    )

    assert state.active is False


def test_high_ias_prevents_activation():
    computer = make_computer()

    state = computer.update(
        make_flight(
            ias=45.0,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert state.active is False


def test_airport_outside_search_radius_prevents_activation():
    database = FakeAirportDatabase(
        distance_nm=2.0,
    )
    computer = make_computer(database)

    state = computer.update(
        make_flight(),
        position_fresh=True,
        airborne=False,
    )

    assert state.active is False


def test_large_airport_elevation_difference_prevents_activation():
    database = FakeAirportDatabase(
        elevation_ft=1000.0,
    )
    computer = make_computer(database)

    state = computer.update(
        make_flight(
            altitude=650.0,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert state.active is False


def test_entry_groundspeed_threshold_is_enforced():
    computer = make_computer()

    state = computer.update(
        make_flight(
            gs=26.0,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert state.active is False


def test_active_state_uses_exit_hysteresis():
    computer = make_computer()

    first = computer.update(
        make_flight(
            gs=20.0,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert first.active is True

    second = computer.update(
        make_flight(
            gs=30.0,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert second.active is True


def test_active_state_deactivates_at_exit_threshold():
    computer = make_computer()

    first = computer.update(
        make_flight(
            gs=20.0,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert first.active is True

    second = computer.update(
        make_flight(
            gs=35.0,
        ),
        position_fresh=True,
        airborne=False,
    )

    assert second.active is False


def test_nonfinite_navigation_input_fails_closed():
    computer = make_computer()

    state = computer.update(
        make_flight(
            altitude=float("nan"),
        ),
        position_fresh=True,
        airborne=False,
    )

    assert state.active is False
