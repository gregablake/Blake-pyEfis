from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_prediction import EnginePredictor


def test_normal_trend_has_no_predicted_exceedance() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        cht_rate=0.1,
        oil_temp_rate=0.1,
        predicted_cht=400.0,
        predicted_oil_temp=220.0,
    )

    result = predictor.predict(trend)

    assert result.severity == "NORMAL"
    assert result.message == "No predicted exceedance."


def test_predicted_cht_limit_creates_caution() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        cht_rate=1.0,
        oil_temp_rate=0.1,
        predicted_cht=435.0,
        predicted_oil_temp=225.0,
    )

    result = predictor.predict(trend)

    assert result.severity == "CAUTION"
    assert "CHT" in result.message


def test_predicted_oil_temp_limit_creates_caution() -> None:
    predictor = EnginePredictor()

    trend = SimpleNamespace(
        cht_rate=0.1,
        oil_temp_rate=1.0,
        predicted_cht=410.0,
        predicted_oil_temp=255.0,
    )

    result = predictor.predict(trend)

    assert result.severity == "CAUTION"
    assert "Oil" in result.message