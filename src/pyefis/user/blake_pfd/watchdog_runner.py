from __future__ import annotations

import sys
from pathlib import Path
from time import monotonic

from pyefis.user.blake_pfd.core.external_watchdog import (
    ExternalWatchdog,
)


HEARTBEAT_PATH = Path(
    "/tmp/blake_pyefis/app.heartbeat"
)


def main() -> int:
    watchdog = ExternalWatchdog(
        HEARTBEAT_PATH,
        stale_after_s=2.0,
    )

    state = watchdog.evaluate(
        monotonic()
    )

    print(
        state.message
    )

    if state.healthy:
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )