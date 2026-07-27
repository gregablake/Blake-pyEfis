from types import SimpleNamespace

import pytest

from pyefis.user.blake_pfd.core.fuel_advisor import (
    FuelAdvisor,
)


def fuel(
    remaining_gal: float,
    flow_gph: float,
):
    return SimpleNamespace(
        remaining_gal=remaining_gal,
        flow_gph=flow_gph,
    )


def navigation(
    distance_nm: float,
):
    return SimpleNamespace(
        distance_nm=distance_nm,
    )


def test_normal_fuel_reserve() -> None:
    advisor = FuelAdvisor()

    result = advisor.advise(
        fuel_state=fuel(
            remaining_gal=20.0,
            flow_gph=8.0,
        ),
        navigation_state=navigation(
            distance_nm=100.0,
        ),
        ground_speed_kt=100.0,
    )

    assert result.severity == "NORMAL"
    assert result.endurance_hr == 2.5
    assert result.time_to_destination_hr == 1.0
    assert result.reserve_at_destination_hr == 1.5
    assert result.fuel_at_destination_gal == 12.0


def test_low_destination_reserve_creates_caution() -> None:
    advisor = FuelAdvisor(
        caution_reserve_min=45.0,
        warning_reserve_min=30.0,
    )

    result = advisor.advise(
        fuel_state=fuel(
            remaining_gal=12.0,
            flow_gph=8.0,
        ),
        navigation_state=navigation(
            distance_nm=90.0,
        ),
        ground_speed_kt=100.0,
    )

    assert result.severity == "CAUTION"
    assert result.title == "Low Fuel Reserve"
    assert result.reserve_at_destination_hr == pytest.approx(
        0.6,
    )


def test_very_low_destination_reserve_creates_warning() -> None:
    advisor = FuelAdvisor()

    result = advisor.advise(
        fuel_state=fuel(
            remaining_gal=10.0,
            flow_gph=8.0,
        ),
        navigation_state=navigation(
            distance_nm=90.0,
        ),
        ground_speed_kt=100.0,
    )

    assert result.severity == "WARNING"
    assert result.reserve_at_destination_hr == pytest.approx(
        0.35,
    )


def test_insufficient_fuel_creates_critical_advice() -> None:
    advisor = FuelAdvisor()

    result = advisor.advise(
        fuel_state=fuel(
            remaining_gal=6.0,
            flow_gph=8.0,
        ),
        navigation_state=navigation(
            distance_nm=100.0,
        ),
        ground_speed_kt=100.0,
    )

    assert result.severity == "CRITICAL"
    assert result.title == (
        "Insufficient Fuel to Destination"
    )

    assert result.reserve_at_destination_hr == pytest.approx(
        -0.25,
    )


def test_low_ground_speed_uses_endurance_only() -> None:
    advisor = FuelAdvisor()

    result = advisor.advise(
        fuel_state=fuel(
            remaining_gal=4.0,
            flow_gph=8.0,
        ),
        navigation_state=navigation(
            distance_nm=100.0,
        ),
        ground_speed_kt=10.0,
    )

    assert result.severity == "CAUTION"
    assert result.title == "Fuel Endurance Caution"
    assert result.time_to_destination_hr is None


def test_missing_fuel_flow_does_not_divide_by_zero() -> None:
    advisor = FuelAdvisor()

    result = advisor.advise(
        fuel_state=fuel(
            remaining_gal=20.0,
            flow_gph=0.0,
        ),
        navigation_state=navigation(
            distance_nm=100.0,
        ),
        ground_speed_kt=100.0,
    )

    assert result.severity == "NORMAL"
    assert result.title == "Fuel Flow Unavailable"
    assert result.endurance_hr is None


def test_nonfinite_inputs_are_safely_rejected() -> None:
    advisor = FuelAdvisor()

    result = advisor.advise(
        fuel_state=fuel(
            remaining_gal=float("nan"),
            flow_gph=8.0,
        ),
        navigation_state=navigation(
            distance_nm=float("inf"),
        ),
        ground_speed_kt=float("nan"),
    )

    assert result.endurance_hr == 0.0
    assert result.severity == "WARNING"


def test_invalid_thresholds_raise_errors() -> None:
    with pytest.raises(
        ValueError,
        match="caution_reserve_min",
    ):
        FuelAdvisor(
            caution_reserve_min=20.0,
            warning_reserve_min=30.0,
        )

    with pytest.raises(
        ValueError,
        match="warning_reserve_min",
    ):
        FuelAdvisor(
            warning_reserve_min=-1.0,
        )