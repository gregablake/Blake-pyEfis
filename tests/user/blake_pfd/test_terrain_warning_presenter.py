from types import SimpleNamespace

from pyefis.user.blake_pfd.core.terrain_warning_presenter import (
    TerrainWarningPresenter,
)


def terrain_alert(
    *,
    active: bool = False,
    warning_level: str = "NONE",
    message: str = "",
    clearance_ft=None,
):
    return SimpleNamespace(
        active=active,
        warning_level=warning_level,
        message=message,
        minimum_clearance_ft=clearance_ft,
    )


def cfit_state(
    *,
    valid: bool = False,
    collision: bool = False,
    seconds=None,
    distance_nm=None,
):
    return SimpleNamespace(
        valid=valid,
        prediction=SimpleNamespace(
            collision_predicted=collision,
            seconds_to_collision=seconds,
            impact_distance_nm=distance_nm,
        ),
    )


def test_no_alert_returns_hidden_presentation() -> None:
    presentation = TerrainWarningPresenter().build(
        terrain_alert_state=terrain_alert(),
        cfit_state=cfit_state(),
    )

    assert presentation.visible is False
    assert presentation.priority == "NONE"


def test_caution_creates_amber_presentation() -> None:
    presentation = TerrainWarningPresenter().build(
        terrain_alert_state=terrain_alert(
            active=True,
            warning_level="CAUTION",
            message="TERRAIN CLEARANCE LOW",
            clearance_ft=800.0,
        ),
        cfit_state=cfit_state(),
    )

    assert presentation.visible is True
    assert presentation.priority == "CAUTION"
    assert presentation.title == "TERRAIN"
    assert (
        presentation.message
        == "TERRAIN CLEARANCE LOW"
    )
    assert (
        presentation.detail
        == "PROJECTED CLEARANCE 800 FT"
    )
    assert presentation.flash is False


def test_warning_creates_red_presentation() -> None:
    presentation = TerrainWarningPresenter().build(
        terrain_alert_state=terrain_alert(
            active=True,
            warning_level="WARNING",
            message="TERRAIN AHEAD",
            clearance_ft=400.0,
        ),
        cfit_state=cfit_state(),
    )

    assert presentation.visible is True
    assert presentation.priority == "WARNING"
    assert presentation.message == "TERRAIN AHEAD"
    assert presentation.flash is False


def test_critical_terrain_alert_flashes() -> None:
    presentation = TerrainWarningPresenter().build(
        terrain_alert_state=terrain_alert(
            active=True,
            warning_level="CRITICAL",
            message="PULL UP",
            clearance_ft=-50.0,
        ),
        cfit_state=cfit_state(),
    )

    assert presentation.visible is True
    assert presentation.priority == "CRITICAL"
    assert presentation.message == "PULL UP"
    assert presentation.flash is True


def test_cfit_prediction_overrides_other_alerts() -> None:
    presentation = TerrainWarningPresenter().build(
        terrain_alert_state=terrain_alert(
            active=True,
            warning_level="CAUTION",
            message="TERRAIN CLEARANCE LOW",
            clearance_ft=800.0,
        ),
        cfit_state=cfit_state(
            valid=True,
            collision=True,
            seconds=45.0,
            distance_nm=1.5,
        ),
    )

    assert presentation.visible is True
    assert presentation.priority == "CRITICAL"
    assert presentation.title == "TERRAIN"
    assert presentation.message == "PULL UP"
    assert "IMPACT 45 SEC" in presentation.detail
    assert "1.5 NM" in presentation.detail
    assert presentation.flash is True


def test_invalid_cfit_does_not_override_warning() -> None:
    presentation = TerrainWarningPresenter().build(
        terrain_alert_state=terrain_alert(
            active=True,
            warning_level="WARNING",
            message="TERRAIN AHEAD",
            clearance_ft=400.0,
        ),
        cfit_state=cfit_state(
            valid=False,
            collision=True,
            seconds=20.0,
        ),
    )

    assert presentation.priority == "WARNING"
    assert presentation.message == "TERRAIN AHEAD"


def test_unknown_alert_level_is_hidden() -> None:
    presentation = TerrainWarningPresenter().build(
        terrain_alert_state=terrain_alert(
            active=True,
            warning_level="UNKNOWN",
            message="UNKNOWN",
        ),
        cfit_state=cfit_state(),
    )

    assert presentation.visible is False