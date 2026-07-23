import pytest

from pyefis.user.blake_pfd.core.rate_of_change import (
    RateOfChangeCalculator,
)
from pyefis.user.blake_pfd.core.rolling_history import (
    RollingHistory,
)


def test_calculates_positive_rate() -> None:
    history = RollingHistory()

    history.add(
        value=100.0,
        timestamp_s=0.0,
    )

    history.add(
        value=120.0,
        timestamp_s=10.0,
    )

    result = RateOfChangeCalculator().calculate(
        history
    )

    assert result.valid is True
    assert result.rate_per_second == 2.0
    assert result.sample_count == 2
    assert result.duration_s == 10.0
    assert result.start_value == 100.0
    assert result.end_value == 120.0


def test_calculates_negative_rate() -> None:
    history = RollingHistory()

    history.add(
        value=250.0,
        timestamp_s=0.0,
    )

    history.add(
        value=230.0,
        timestamp_s=10.0,
    )

    result = RateOfChangeCalculator().calculate(
        history
    )

    assert result.valid is True
    assert result.rate_per_second == -2.0


def test_constant_value_has_zero_rate() -> None:
    history = RollingHistory()

    history.add(
        value=200.0,
        timestamp_s=0.0,
    )

    history.add(
        value=200.0,
        timestamp_s=10.0,
    )

    result = RateOfChangeCalculator().calculate(
        history
    )

    assert result.valid is True
    assert result.rate_per_second == 0.0


def test_empty_history_returns_invalid_result() -> None:
    history = RollingHistory()

    result = RateOfChangeCalculator().calculate(
        history
    )

    assert result.valid is False
    assert result.sample_count == 0
    assert result.duration_s == 0.0
    assert result.start_value is None
    assert result.end_value is None


def test_single_sample_returns_invalid_result() -> None:
    history = RollingHistory()

    history.add(
        value=100.0,
        timestamp_s=5.0,
    )

    result = RateOfChangeCalculator().calculate(
        history
    )

    assert result.valid is False
    assert result.sample_count == 1
    assert result.start_value == 100.0
    assert result.end_value == 100.0


def test_short_duration_returns_invalid_result() -> None:
    history = RollingHistory()

    history.add(
        value=100.0,
        timestamp_s=0.0,
    )

    history.add(
        value=120.0,
        timestamp_s=0.5,
    )

    result = RateOfChangeCalculator(
        minimum_duration_s=1.0,
    ).calculate(history)

    assert result.valid is False
    assert result.duration_s == 0.5


def test_custom_minimum_sample_count_is_enforced() -> None:
    history = RollingHistory()

    history.add(
        value=100.0,
        timestamp_s=0.0,
    )

    history.add(
        value=110.0,
        timestamp_s=1.0,
    )

    result = RateOfChangeCalculator(
        minimum_samples=3,
    ).calculate(history)

    assert result.valid is False
    assert result.sample_count == 2


def test_invalid_minimum_samples_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="minimum_samples",
    ):
        RateOfChangeCalculator(
            minimum_samples=1,
        )


def test_invalid_minimum_duration_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="minimum_duration_s",
    ):
        RateOfChangeCalculator(
            minimum_duration_s=0.0,
        )