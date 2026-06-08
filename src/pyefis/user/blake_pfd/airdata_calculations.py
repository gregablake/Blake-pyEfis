from math import sqrt

KNOTS_PER_MPS = 1.94384

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