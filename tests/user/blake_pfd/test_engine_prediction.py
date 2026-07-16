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