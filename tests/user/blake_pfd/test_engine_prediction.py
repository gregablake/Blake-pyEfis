from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_prediction import EnginePredictor


def test_normal_trend_has_no_predicted_exceedance() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        current_cht=390.0,
        current_oil_temp=220.0,
        cht_rate=0.1,
        oil_temp_rate=0.1,
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
    )

    result = predictor.predict(trend)

    assert result.time_to_cht_limit_s == 30.0
    assert result.time_to_oil_temp_limit_s == 10.0
    assert result.severity == "CAUTION"
    assert "Oil" in result.message