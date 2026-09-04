from math import isfinite, sqrt

KNOTS_PER_MPS = 1.94384
PASCALS_PER_INHG = 3386.389


def indicated_airspeed_from_dp(dp_pa: float) -> float:
    """
    Differential pressure -> IAS
    """
    if dp_pa <= 0:
        return 0.0

    rho = 1.225

    v_ms = sqrt((2 * dp_pa) / rho)

    return v_ms * KNOTS_PER_MPS


def pressure_altitude(static_pa: float) -> float:
    """
    Pressure altitude in feet
    """

    return (
        145366.45 *
        (
            1 -
            (static_pa / 101325.0) ** 0.190284
        )
    )


def indicated_altitude(
    static_pa: float,
    baro_setting_inhg: float,
) -> float:
    """
    Barometric indicated altitude in feet using the
    selected altimeter setting.
    """
    if (
        not isfinite(static_pa)
        or static_pa <= 0.0
    ):
        raise ValueError(
            "static pressure must be finite and positive"
        )

    if (
        not isfinite(baro_setting_inhg)
        or baro_setting_inhg <= 0.0
    ):
        raise ValueError(
            "altimeter setting must be finite and positive"
        )

    reference_pressure_pa = (
        baro_setting_inhg * PASCALS_PER_INHG
    )

    return (
        145366.45 *
        (
            1 -
            (
                static_pa /
                reference_pressure_pa
            ) ** 0.190284
        )
    )
