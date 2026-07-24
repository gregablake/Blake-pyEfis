from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_prediction import EnginePredictor


def test_normal_trend_has_no_predicted_exceedance() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=390.0,
        current_oil_temp=220.0,
        cht_rate=0.1,
        oil_temp_rate=0.1,
        sample_count=5,
        history_duration_s=5.0,
    )

    result = predictor.predict(trend)

    assert result.severity == "NORMAL"
    assert result.message == "No predicted exceedance."


def test_predicted_cht_limit_creates_caution() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=390.0,
        current_oil_temp=220.0,
        cht_rate=1.0,
        oil_temp_rate=0.1,
        sample_count=5,
        history_duration_s=5.0,
    )

    result = predictor.predict(trend)

    assert result.severity == "CAUTION"
    assert "CHT" in result.message
    assert result.time_to_cht_limit_s == 40.0


def test_predicted_oil_temp_limit_creates_caution() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=400.0,
        current_oil_temp=230.0,
        cht_rate=0.1,
        oil_temp_rate=1.0,
        sample_count=5,
        history_duration_s=5.0,
    )

    result = predictor.predict(trend)

    assert result.severity == "CAUTION"
    assert "Oil" in result.message
    assert result.time_to_oil_temp_limit_s == 20.0
    
def test_most_urgent_predicted_limit_is_reported() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=400.0,
        current_oil_temp=230.0,
        cht_rate=1.0,
        oil_temp_rate=2.0,
        sample_count=5,
        history_duration_s=5.0,
    )

    result = predictor.predict(trend)

    assert result.time_to_cht_limit_s == 30.0
    assert result.time_to_oil_temp_limit_s == 10.0
    assert result.severity == "CAUTION"
    assert "Oil" in result.message
    
def test_prediction_waits_for_minimum_samples() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=420.0,
        current_oil_temp=240.0,
        cht_rate=2.0,
        oil_temp_rate=2.0,
        sample_count=2,
        history_duration_s=1.0,
    )

    result = predictor.predict(trend)

    assert result.severity == "NORMAL"
    assert result.message == "Collecting trend data."
    
def test_prediction_waits_for_minimum_history_duration() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=420.0,
        current_oil_temp=240.0,
        cht_rate=2.0,
        oil_temp_rate=2.0,
        sample_count=5,
        history_duration_s=0.5,
    )

    result = predictor.predict(trend)

    assert result.severity == "NORMAL"
    assert result.message == "Collecting trend history."
    
def test_prediction_reports_full_confidence() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=400.0,
        current_oil_temp=230.0,
        cht_rate=1.0,
        oil_temp_rate=2.0,
        sample_count=20,
        history_duration_s=10.0,
    )

    result = predictor.predict(trend)

    assert result.confidence == 1.0
    
    
def test_prediction_preserves_sensor_rates() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=390.0,
        current_oil_temp=220.0,
        cht_rate=1.5,
        oil_temp_rate=0.75,
        sample_count=20,
        history_duration_s=10.0,
    )

    result = predictor.predict(trend)

    assert result.cht_rate_f_per_s == 1.5
    assert result.oil_temp_rate_f_per_s == 0.75
    assert "1.5F/s" in result.message


def test_cht_is_reported_when_more_urgent_than_oil() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=420.0,
        current_oil_temp=220.0,
        cht_rate=2.0,
        oil_temp_rate=1.0,
        sample_count=20,
        history_duration_s=10.0,
    )

    result = predictor.predict(trend)

    assert result.time_to_cht_limit_s == 5.0
    assert result.time_to_oil_temp_limit_s == 30.0
    assert result.severity == "CAUTION"
    assert result.message.startswith("CHT rising")


def test_oil_is_reported_when_more_urgent_than_cht() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=400.0,
        current_oil_temp=240.0,
        cht_rate=1.0,
        oil_temp_rate=2.0,
        sample_count=20,
        history_duration_s=10.0,
    )

    result = predictor.predict(trend)

    assert result.time_to_cht_limit_s == 30.0
    assert result.time_to_oil_temp_limit_s == 5.0
    assert result.severity == "CAUTION"
    assert result.message.startswith(
        "Oil temperature rising"
    )


def test_already_exceeded_limit_reports_zero_seconds() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=435.0,
        current_oil_temp=220.0,
        cht_rate=1.0,
        oil_temp_rate=0.0,
        sample_count=20,
        history_duration_s=10.0,
    )

    result = predictor.predict(trend)

    assert result.time_to_cht_limit_s == 0.0
    assert result.severity == "CAUTION"
    assert "limit in 0s" in result.message
    
def test_low_confidence_prediction_does_not_create_caution() -> None:
    predictor = EnginePredictor(
        minimum_confidence=0.10,
    )

    trend = SimpleNamespace(
        current_cht=420.0,
        current_oil_temp=220.0,
        cht_rate=5.0,
        oil_temp_rate=0.0,
        sample_count=5,
        history_duration_s=2.0,
    )

    result = predictor.predict(trend)

    assert result.time_to_cht_limit_s == 2.0
    assert result.confidence == 0.05
    assert result.severity == "NORMAL"
    assert result.message == (
        "Potential limit trend detected; "
        "collecting prediction confidence."
    )


def test_prediction_activates_after_confidence_threshold() -> None:
    predictor = EnginePredictor(
        minimum_confidence=0.10,
    )

    trend = SimpleNamespace(
        current_cht=420.0,
        current_oil_temp=220.0,
        cht_rate=2.0,
        oil_temp_rate=0.0,
        sample_count=5,
        history_duration_s=5.0,
    )

    result = predictor.predict(trend)

    assert result.confidence == 0.125
    assert result.severity == "CAUTION"
    assert result.message.startswith("CHT rising")


def test_custom_prediction_confidence_threshold() -> None:
    predictor = EnginePredictor(
        minimum_confidence=0.50,
    )

    trend = SimpleNamespace(
        current_cht=420.0,
        current_oil_temp=220.0,
        cht_rate=2.0,
        oil_temp_rate=0.0,
        sample_count=10,
        history_duration_s=10.0,
    )

    result = predictor.predict(trend)

    assert result.confidence == 0.5
    assert result.severity == "CAUTION"


def test_invalid_prediction_confidence_threshold_raises_error() -> None:
    import pytest

    with pytest.raises(
        ValueError,
        match="minimum_confidence",
    ):
        EnginePredictor(
            minimum_confidence=1.1,
        )


def test_prediction_activates_after_confidence_threshold() -> None:
    predictor = EnginePredictor(
        minimum_confidence=0.10,
    )

    trend = SimpleNamespace(
        current_cht=420.0,
        current_oil_temp=220.0,
        cht_rate=2.0,
        oil_temp_rate=0.0,
        sample_count=5,
        history_duration_s=5.0,
    )

    result = predictor.predict(trend)

    assert result.confidence == 0.125
    assert result.severity == "CAUTION"
    assert result.message.startswith("CHT rising")


def test_invalid_prediction_confidence_threshold_raises_error() -> None:
    import pytest

    with pytest.raises(
        ValueError,
        match="minimum_confidence",
    ):
        EnginePredictor(
            minimum_confidence=1.1,
        )