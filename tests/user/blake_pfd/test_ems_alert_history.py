import csv
from types import SimpleNamespace

from pyefis.user.blake_pfd.ems_alert_history import EmsAlertHistory


class DummyWarning:
    def __init__(self, text: str) -> None:
        self.text = text


def test_update_writes_new_alerts_to_csv(tmp_path, monkeypatch) -> None:
    history = EmsAlertHistory(max_alerts=10)
    history.log_path = tmp_path / "ems_alert_history.csv"

    monkeypatch.setattr(
        "pyefis.user.blake_pfd.ems_alert_history.get_engine_warnings",
        lambda engine: [DummyWarning("LOW OIL")],
    )

    history.update(SimpleNamespace())

    with history.log_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["alert"] == "LOW OIL"
