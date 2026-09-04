from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafeTaxiInputState:
    position_fresh: bool
    airborne_inhibit: bool


def evaluate_safe_taxi_inputs(
    *,
    watchdog,
    flight_state,
) -> SafeTaxiInputState:
    """
    Convert live PFD/watchdog state into the minimal
    fail-closed inputs required by Safe Taxi.

    Any missing or false validity/freshness information
    prevents Safe Taxi from taking over the primary display.
    """

    if watchdog is None:
        return SafeTaxiInputState(
            position_fresh=False,
            airborne_inhibit=True,
        )

    position_valid = bool(
        getattr(
            watchdog,
            "position_valid",
            False,
        )
    )

    position_is_fresh = bool(
        getattr(
            watchdog,
            "position_fresh",
            False,
        )
    )

    air_data_valid = bool(
        getattr(
            watchdog,
            "air_data_valid",
            False,
        )
    )

    air_data_fresh = bool(
        getattr(
            watchdog,
            "air_data_fresh",
            False,
        )
    )

    position_fresh = (
        position_valid
        and position_is_fresh
    )

    # A missing flight-state object is deliberately
    # interpreted as airborne/inhibited.
    airborne = True

    if flight_state is not None:
        airborne = bool(
            getattr(
                flight_state,
                "airborne",
                True,
            )
        )

    airborne_inhibit = (
        airborne
        or not air_data_valid
        or not air_data_fresh
    )

    return SafeTaxiInputState(
        position_fresh=position_fresh,
        airborne_inhibit=airborne_inhibit,
    )


def safe_taxi_takeover_allowed(
    *,
    feature_enabled: bool,
    auto_switch_enabled: bool,
    taxi_active: bool,
    safety: SafeTaxiInputState,
) -> bool:
    """
    Final authority for allowing the Safe Taxi page
    to replace the primary flight display.

    Every condition must positively permit takeover.
    """

    if safety is None:
        return False

    return bool(
        feature_enabled
        and auto_switch_enabled
        and taxi_active
        and safety.position_fresh
        and not safety.airborne_inhibit
    )
