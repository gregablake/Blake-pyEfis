import pytest

from pyefis.user.blake_pfd.core.sensor_trend_predictor import (
    SensorTrendPredictor,
)


def test_predictor_waits_for_enough_history() -> None:
    predictor = SensorTrendPredictor(
        minimum_samples=3,
        minimum_duration_s=2.0,
    )

    result = predictor.update(
        value=400.0,
        limit_value=450.0,
        timestamp_s=0.0,
    )

    assert result.valid is False
    assert result.current_value == 400.0
    assert result.rate.valid is False
    assert result.limit.valid is False


def test_predictor_calculates_rate_and_time_to_limit() -> None:
    predictor = SensorTrendPredictor(
        minimum_samples=3,
        minimum_duration_s=2.0,
    )

    predictor.update(
        value=400.0,
        limit_value=450.0,
        timestamp_s=0.0,
    )

    predictor.update(
        value=410.0,
        limit_value=450.0,
        timestamp_s=1.0,
    )

    result = predictor.update(
        value=420.0,
        limit_value=450.0,
        timestamp_s=2.0,
    )

    assert result.valid is True
    assert result.rate.valid is True
    assert result.rate.rate_per_second == 10.0
    assert result.limit.approaching_limit is True
    assert result.limit.time_to_limit_s == 3.0


def test_predictor_handles_falling_value() -> None:
    predictor = SensorTrendPredictor(
        minimum_samples=3,
        minimum_duration_s=2.0,
    )

    predictor.update(
        value=430.0,
        limit_value=450.0,
        timestamp_s=0.0,
    )

    predictor.update(
        value=425.0,
        limit_value=450.0,
        timestamp_s=1.0,
    )

    result = predictor.update(
        value=420.0,
        limit_value=450.0,
        timestamp_s=2.0,
    )

    assert result.valid is True
    assert result.rate.rate_per_second == -5.0
    assert result.limit.approaching_limit is False
    assert result.limit.time_to_limit_s is None


def test_predictor_reports_exceeded_limit() -> None:
    predictor = SensorTrendPredictor(
        minimum_samples=2,
        minimum_duration_s=1.0,
    )

    predictor.update(
        value=445.0,
        limit_value=450.0,
        timestamp_s=0.0,
    )

    result = predictor.update(
        value=455.0,
        limit_value=450.0,
        timestamp_s=1.0,
    )

    assert result.valid is True
    assert result.limit.already_exceeded is True
    assert result.limit.time_to_limit_s == 0.0


def test_confidence_increases_with_more_history() -> None:
    predictor = SensorTrendPredictor(
        minimum_samples=2,
        minimum_duration_s=1.0,
    )

    first = predictor.update(
        value=400.0,
        limit_value=450.0,
        timestamp_s=0.0,
    )

    predictor.update(
        value=405.0,
        limit_value=450.0,
        timestamp_s=1.0,
    )

    later = predictor.update(
        value=410.0,
        limit_value=450.0,
        timestamp_s=2.0,
    )

    assert later.confidence > first.confidence
    assert 0.0 <= later.confidence <= 1.0


def test_clear_resets_history() -> None:
    predictor = SensorTrendPredictor()

    predictor.update(
        value=400.0,
        limit_value=450.0,
        timestamp_s=0.0,
    )

    predictor.clear()

    assert predictor.history.sample_count == 0


def test_window_trims_old_samples() -> None:
    predictor = SensorTrendPredictor(
        window_s=5.0,
        minimum_samples=2,
        minimum_duration_s=1.0,
    )

    predictor.update(
        value=400.0,
        limit_value=450.0,
        timestamp_s=0.0,
    )

    predictor.update(
        value=410.0,
        limit_value=450.0,
        timestamp_s=4.0,
    )

    result = predictor.update(
        value=420.0,
        limit_value=450.0,
        timestamp_s=6.0,
    )

    assert result.rate.start_value == 410.0
    assert result.rate.end_value == 420.0
    assert result.rate.duration_s == 2.0
    assert result.rate.rate_per_second == pytest.approx(
        5.0,
    )