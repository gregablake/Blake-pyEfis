from types import SimpleNamespace

import pyefis.user.blake_pfd.core.engine_trend_manager as trend_module
from pyefis.user.blake_pfd.core.engine_trend_manager import EngineTrendManager


def engine(
    cht: float,
    oil_temp: float,
    oil_pressure: float = 45.0,
):
    return SimpleNamespace(
        cht_f=[cht],
        oil_temp_f=oil_temp,
        oil_pressure_psi=oil_pressure,
    )


def test_engine_trend_uses_elapsed_time(monkeypatch) -> None:
    times = iter([100.0, 105.0])
    monkeypatch.setattr(trend_module, "monotonic", lambda: next(times))

    manager = EngineTrendManager(history_seconds=10.0)

    manager.update(engine(400.0, 220.0))
    result = manager.update(engine(410.0, 225.0))

    assert result.cht_rate == 2.0
    assert result.oil_temp_rate == 1.0
    assert result.predicted_cht == 470.0
    assert result.predicted_oil_temp == 255.0
    assert result.warning == "Oil temperature rising."


def test_single_sample_has_zero_rates(monkeypatch) -> None:
    monkeypatch.setattr(trend_module, "monotonic", lambda: 100.0)

    manager = EngineTrendManager()

    result = manager.update(engine(400.0, 220.0))

    assert result.cht_rate == 0.0
    assert result.oil_temp_rate == 0.0
    assert result.oil_pressure_rate == 0.0