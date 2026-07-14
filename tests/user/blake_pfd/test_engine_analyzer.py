from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_analyzer import EngineAnalyzer


def engine(
    oil_pressure: float = 45.0,
    oil_temp: float = 210.0,
    cht: list[float] | None = None,
    egt: list[float] | None = None,
    alternator_online: bool = True,
):
    return SimpleNamespace(
        oil_pressure_psi=oil_pressure,
        oil_temp_f=oil_temp,
        cht_f=cht or [350.0] * 6,
        egt_f=egt or [1350.0] * 6,
        alternator_online=alternator_online,
    )


def test_normal_engine_analysis() -> None:
    analyzer = EngineAnalyzer()

    result = analyzer.analyze(engine())

    assert result.severity == "NORMAL"
    assert "normally" in result.summary.lower()


def test_low_oil_pressure_is_critical() -> None:
    analyzer = EngineAnalyzer()

    result = analyzer.analyze(
        engine(oil_pressure=12.0)
    )

    assert result.severity == "CRITICAL"
    assert "oil pressure" in result.summary.lower()


def test_high_cht_is_critical() -> None:
    analyzer = EngineAnalyzer()

    result = analyzer.analyze(
        engine(cht=[350.0, 360.0, 455.0, 365.0, 370.0, 355.0])
    )

    assert result.severity == "CRITICAL"
    assert result.hottest_cylinder == 3
    assert result.hottest_cht_f == 455.0


def test_elevated_egt_spread_is_caution() -> None:
    analyzer = EngineAnalyzer()

    result = analyzer.analyze(
        engine(egt=[1300.0, 1320.0, 1500.0, 1310.0, 1330.0, 1340.0])
    )

    assert result.severity == "CAUTION"
    assert "egt spread" in result.summary.lower()


def test_alternator_offline_is_caution() -> None:
    analyzer = EngineAnalyzer()

    result = analyzer.analyze(
        engine(alternator_online=False)
    )

    assert result.severity == "CAUTION"
    assert "alternator" in result.summary.lower()