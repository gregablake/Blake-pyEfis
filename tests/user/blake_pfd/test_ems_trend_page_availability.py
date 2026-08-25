from __future__ import annotations

from pyefis.user.blake_pfd.ems_trend_page import (
    EmsTrendPage,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_trend_page_can_mark_current_ems_data_unavailable() -> None:
    page = EmsTrendPage()

    page.add_sample(
        EngineData(
            rpm=2400.0,
            oil_temp_f=190.0,
            oil_pressure_psi=45.0,
            cht_f=[
                350.0,
                350.0,
                350.0,
                350.0,
                350.0,
                350.0,
            ],
            egt_f=[
                1350.0,
                1350.0,
            ],
        )
    )

    assert len(page.samples) == 1

    page.set_data_available(
        False,
        message="EMS DATA STALE",
    )

    assert page.data_available is False
    assert page.fault_message == "EMS DATA STALE"

    # Historical samples should remain available for review.
    assert len(page.samples) == 1