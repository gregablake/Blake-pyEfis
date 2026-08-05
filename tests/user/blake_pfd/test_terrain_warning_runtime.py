from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_warning_presenter import (
    TerrainWarningPresenter,
)


def test_runtime_banner_builds():

    terrain = SimpleNamespace(
        active=True,
        warning_level="WARNING",
        message="TERRAIN AHEAD",
        minimum_clearance_ft=350,
    )

    cfit = SimpleNamespace(
        valid=False,
        prediction=SimpleNamespace(
            collision_predicted=False,
        ),
    )

    banner = (
        TerrainWarningPresenter().build(
            terrain_alert_state=terrain,
            cfit_state=cfit,
        )
    )

    assert banner.visible
    assert banner.priority == "WARNING"