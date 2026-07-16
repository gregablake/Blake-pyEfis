from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_manager import EngineManager


def engine(**overrides):
    values = {
        "oil_pressure_psi": 45.0,
        "oil_temp_f": 210.0,
        "cht_f": [350.0] * 6,
        "egt_f": [1350.0] * 6,
        "alternator_online": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_normal_engine_health() -> None:
    manager = EngineManager()

    result = manager.update(engine())

    assert result.health_score == 100
    assert result.status == "NORMAL"
    assert result.cht_max_f == 350.0
    assert result.cht_spread_f == 0.0


def test_low_oil_pressure_reduces_health() -> None:
    manager = EngineManager()

    result = manager.update(
        engine(oil_pressure_psi=12.0)
    )

    assert result.health_score == 60
    assert result.status == "CRITICAL"
    assert result.oil_pressure_margin_psi == -3.0


def test_high_oil_temperature_is_critical() -> None:
    manager = EngineManager()

    result = manager.update(
        engine(oil_temp_f=265.0)
    )

    assert result.health_score == 65
    assert result.status == "CRITICAL"
    assert result.oil_temp_margin_f == -5.0


def test_high_cht_is_critical() -> None:
    manager = EngineManager()

    result = manager.update(
        engine(
            cht_f=[350.0, 360.0, 455.0, 365.0, 370.0, 355.0]
        )
    )

    assert result.health_score == 65
    assert result.status == "CRITICAL"
    assert result.cht_max_f == 455.0
    assert result.cht_spread_f == 105.0


def test_multiple_faults_never_create_negative_score() -> None:
    manager = EngineManager()

    result = manager.update(
        engine(
            oil_pressure_psi=5.0,
            oil_temp_f=275.0,
            cht_f=[460.0] * 6,
            egt_f=[1650.0] * 6,
            alternator_online=False,
        )
    )

    assert result.health_score == 0
    assert result.status == "CAUTION" or result.status == "CRITICAL"