from types import SimpleNamespace

from pyefis.user.blake_pfd.core.engine_manager import EngineManager


def test_critical_status_is_not_downgraded_by_later_caution() -> None:
    manager = EngineManager()

    engine = SimpleNamespace(
        oil_pressure_psi=5.0,
        oil_temp_f=275.0,
        cht_f=[460.0] * 6,
        egt_f=[1650.0] * 6,
        alternator_online=False,
    )

    result = manager.update(engine)

    assert result.health_score == 0
    assert result.status == "CRITICAL"