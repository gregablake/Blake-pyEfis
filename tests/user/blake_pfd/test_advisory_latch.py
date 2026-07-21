from pyefis.user.blake_pfd.core.advisory_latch import (
    AdvisoryLatch,
)


def test_advisory_requires_multiple_samples_to_activate() -> None:
    latch = AdvisoryLatch(
        activate_samples=3,
        clear_samples=5,
    )

    latch.update("high_cht", "CAUTION")
    assert latch.state.active_key is None

    latch.update("high_cht", "CAUTION")
    assert latch.state.active_key is None

    latch.update("high_cht", "CAUTION")
    assert latch.state.active_key == "high_cht"
    assert latch.state.active_severity == "CAUTION"


def test_active_advisory_requires_multiple_clear_samples() -> None:
    latch = AdvisoryLatch(
        activate_samples=1,
        clear_samples=3,
    )

    latch.update("high_cht", "CAUTION")

    first_clear = latch.update(None, "NORMAL")
    second_clear = latch.update(None, "NORMAL")
    third_clear = latch.update(None, "NORMAL")

    assert first_clear.active_key == "high_cht"
    assert second_clear.active_key == "high_cht"
    assert third_clear.active_key is None
    assert third_clear.active_severity == "NORMAL"


def test_higher_severity_activates_immediately() -> None:
    latch = AdvisoryLatch(
        activate_samples=3,
        clear_samples=5,
    )

    latch.update("high_cht", "CAUTION")
    latch.update("high_cht", "CAUTION")
    latch.update("high_cht", "CAUTION")

    result = latch.update(
        "low_oil_pressure",
        "CRITICAL",
    )

    assert result.active_key == "low_oil_pressure"
    assert result.active_severity == "CRITICAL"


def test_invalid_severity_is_treated_as_normal() -> None:
    latch = AdvisoryLatch(
        activate_samples=1,
        clear_samples=1,
    )

    result = latch.update(
        "unknown",
        "BANANA",
    )

    assert result.active_key is None
    assert result.active_severity == "NORMAL"


def test_invalid_constructor_values_raise_error() -> None:
    try:
        AdvisoryLatch(activate_samples=0)
    except ValueError as exc:
        assert "activate_samples" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

    try:
        AdvisoryLatch(clear_samples=0)
    except ValueError as exc:
        assert "clear_samples" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
    
def test_same_severity_new_advisory_does_not_replace_immediately() -> None:
    latch = AdvisoryLatch(
        activate_samples=3,
        clear_samples=5,
    )

    latch.update("high_cht", "CAUTION")
    latch.update("high_cht", "CAUTION")
    latch.update("high_cht", "CAUTION")

    assert latch.state.active_key == "high_cht"

    latch.update("high_oil_temp", "CAUTION")

    assert latch.state.active_key == "high_cht"
    assert latch.state.active_severity == "CAUTION"
    
def test_higher_severity_replaces_active_advisory_immediately() -> None:
    latch = AdvisoryLatch(
        activate_samples=3,
        clear_samples=5,
    )

    latch.update("high_cht", "CAUTION")
    latch.update("high_cht", "CAUTION")
    latch.update("high_cht", "CAUTION")

    assert latch.state.active_key == "high_cht"

    latch.update(
        "low_oil_pressure",
        "CRITICAL",
    )

    assert latch.state.active_key == "low_oil_pressure"
    assert latch.state.active_severity == "CRITICAL"