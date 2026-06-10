from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.database_importer import AviationDatabase


@dataclass
class StartupStatus:
    config_ok: bool = False
    database_ok: bool = False
    airports_loaded: int = 0
    navaids_loaded: int = 0
    status_text: str = "UNKNOWN"


def run_startup_check() -> StartupStatus:
    try:
        config = load_config()
        config_ok = config is not None
    except Exception:
        config_ok = False

    airports_loaded = 0
    navaids_loaded = 0
    database_ok = False

    try:
        db = AviationDatabase()
        db.load_all()
        airports_loaded = len(db.airports)
        navaids_loaded = len(db.navaids)
        database_ok = airports_loaded > 0
    except Exception:
        database_ok = False

    if config_ok and database_ok:
        status_text = "SYSTEM READY"
    elif config_ok:
        status_text = "CONFIG OK / DATABASE FAIL"
    else:
        status_text = "CONFIG FAIL"

    return StartupStatus(
        config_ok=config_ok,
        database_ok=database_ok,
        airports_loaded=airports_loaded,
        navaids_loaded=navaids_loaded,
        status_text=status_text,
    )


def demo() -> None:
    print(run_startup_check())


if __name__ == "__main__":
    demo()