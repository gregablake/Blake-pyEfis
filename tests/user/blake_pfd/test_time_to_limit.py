import pytest

from pyefis.user.blake_pfd.core.rate_of_change import (
    RateOfChangeResult,
)
from pyefis.user.blake_pfd.core.time_to_limit import (
    TimeToLimitCalculator,
)


def valid_rate(
    rate_per_second: float,
) -> RateOfChangeResult:
    return RateOfChangeResult(
        rate_per_second=rate_per_second,
        sample_count=5,
        duration_s=10.0,
        start_value=100.0,
        end_value=110.0,
        valid=True,
    )


def test_calculates_time_to_limit() -> None:
    calculator = TimeToLimitCalculator()

    result = calculator.calculate(
        current_value=420.0,
        limit_value=450.0,
        rate=valid_rate(2.0),
    )

    assert result.valid is True
    assert result.approaching_limit is True
    assert result.already_exceeded is False
    assert result.time_to_limit_s == 15.0


def test_limit_already_exceeded_returns_zero_seconds() -> None:
    calculator = TimeToLimitCalculator()

    result = calculator.calculate(
        current_value=455.0,
        limit_value=450.0,
        rate=valid_rate(2.0),
    )

    assert result.valid is True
    assert result.approaching_limit is True
    assert result.already_exceeded is True
    assert result.time_to_limit_s == 0.0


def test_value_exactly_at_limit_is_exceeded() -> None:
    calculator = TimeToLimitCalculator()

    result = calculator.calculate(
        current_value=450.0,
        limit_value=450.0,
        rate=valid_rate(1.0),
    )

    assert result.already_exceeded is True
    assert result.time_to_limit_s == 0.0


def test_falling_value_is_not_approaching_upper_limit() -> None:
    calculator = TimeToLimitCalculator()

    result = calculator.calculate(
        current_value=420.0,
        limit_value=450.0,
        rate=valid_rate(-2.0),
    )

    assert result.valid is True
    assert result.approaching_limit is False
    assert result.already_exceeded is False
    assert result.time_to_limit_s is None


def test_zero_rate_is_not_approaching_limit() -> None:
    calculator = TimeToLimitCalculator()

    result = calculator.calculate(
        current_value=420.0,
        limit_value=450.0,
        rate=valid_rate(0.0),
    )

    assert result.valid is True
    assert result.approaching_limit is False
    assert result.time_to_limit_s is None


def test_invalid_rate_returns_invalid_prediction() -> None:
    calculator = TimeToLimitCalculator()

    result = calculator.calculate(
        current_value=420.0,
        limit_value=450.0,
        rate=RateOfChangeResult(),
    )

    assert result.valid is False
    assert result.approaching_limit is False
    assert result.time_to_limit_s is None


def test_fractional_prediction_is_preserved() -> None:
    calculator = TimeToLimitCalculator()

    result = calculator.calculate(
        current_value=425.0,
        limit_value=450.0,
        rate=valid_rate(3.0),
    )

    assert result.time_to_limit_s == pytest.approx(
        8.3333333333,
    )