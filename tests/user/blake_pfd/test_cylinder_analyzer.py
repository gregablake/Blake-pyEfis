from types import SimpleNamespace

from pyefis.user.blake_pfd.core.cylinder_analyzer import CylinderAnalyzer


def engine(
    cht: list[float] | None = None,
    egt: list[float] | None = None,
):
    return SimpleNamespace(
        cht_f=cht or [350.0] * 6,
        egt_f=egt or [1350.0] * 6,
    )


def test_balanced_cylinders() -> None:
    analyzer = CylinderAnalyzer()

    result = analyzer.analyze(
        engine(
            cht=[350.0, 355.0, 352.0, 358.0, 354.0, 351.0],
            egt=[1340.0, 1360.0, 1350.0, 1370.0, 1355.0, 1345.0],
        )
    )

    assert result.imbalance_detected is False
    assert result.message == "Cylinders balanced."
    assert result.hottest_cylinder == 4
    assert result.hottest_cht_f == 358.0


def test_large_cht_spread_detects_imbalance() -> None:
    analyzer = CylinderAnalyzer()

    result = analyzer.analyze(
        engine(
            cht=[340.0, 350.0, 410.0, 355.0, 345.0, 360.0],
        )
    )

    assert result.imbalance_detected is True
    assert result.cht_spread_f == 70.0
    assert "imbalance" in result.message.lower()


def test_large_egt_spread_detects_imbalance() -> None:
    analyzer = CylinderAnalyzer()

    result = analyzer.analyze(
        engine(
            egt=[1250.0, 1300.0, 1450.0, 1280.0, 1320.0, 1290.0],
        )
    )

    assert result.imbalance_detected is True
    assert result.egt_spread_f == 200.0


def test_empty_sensor_lists_are_safe() -> None:
    analyzer = CylinderAnalyzer()

    result = analyzer.analyze(
        SimpleNamespace(
            cht_f=[],
            egt_f=[],
        )
    )

    assert result.hottest_cylinder == 0
    assert result.hottest_cht_f == 0.0
    assert result.cht_spread_f == 0.0
    assert result.egt_spread_f == 0.0
    assert result.imbalance_detected is False