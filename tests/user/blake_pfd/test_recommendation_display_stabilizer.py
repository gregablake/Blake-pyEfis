from types import SimpleNamespace

from pyefis.user.blake_pfd.core.recommendation_display_stabilizer import (
    RecommendationDisplayStabilizer,
)


def recommendation(
    severity: str,
    title: str,
):
    return SimpleNamespace(
        severity=severity,
        title=title,
        urgency_s=None,
        confidence=None,
    )


def test_caution_requires_multiple_samples_to_display() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_samples=3,
        clear_samples=5,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    assert stabilizer.update(caution) is None
    assert stabilizer.update(caution) is None
    assert stabilizer.update(caution) is caution


def test_warning_displays_immediately() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_samples=3,
        clear_samples=5,
    )

    warning = recommendation(
        "WARNING",
        "Engine Warning",
    )

    assert stabilizer.update(warning) is warning


def test_critical_condition_displays_immediately() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_samples=3,
        clear_samples=5,
    )

    critical = recommendation(
        "CRITICAL",
        "Oil Pressure Advisor",
    )

    assert stabilizer.update(critical) is critical


def test_active_caution_requires_multiple_clear_samples() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_samples=1,
        clear_samples=3,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    normal = recommendation(
        "NORMAL",
        "Normal",
    )

    assert stabilizer.update(caution) is caution
    assert stabilizer.update(normal) is caution
    assert stabilizer.update(normal) is caution
    assert stabilizer.update(normal) is None


def test_new_caution_replaces_old_after_persisting() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_samples=3,
        clear_samples=5,
    )

    cht = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    oil = recommendation(
        "CAUTION",
        "Oil Temperature Advisor",
    )

    stabilizer.update(cht)
    stabilizer.update(cht)
    assert stabilizer.update(cht) is cht

    assert stabilizer.update(oil) is cht
    assert stabilizer.update(oil) is cht
    assert stabilizer.update(oil) is oil


def test_warning_clears_stale_latched_caution() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_samples=1,
        clear_samples=3,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    warning = recommendation(
        "WARNING",
        "Engine Warning",
    )

    normal = recommendation(
        "NORMAL",
        "Normal",
    )

    assert stabilizer.update(caution) is caution
    assert stabilizer.update(warning) is warning
    assert stabilizer.update(normal) is None