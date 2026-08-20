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

STARTUP_MARKER_PATH = Path(
    "/tmp/blake_pyefis/app.started"
)

STARTUP_GRACE_S = 5.0


def main() -> int:
    now_s = monotonic()

    if not HEARTBEAT_PATH.exists():
        try:
            startup_text = (
                STARTUP_MARKER_PATH.read_text(
                    encoding="utf-8",
                )
            )

            startup_s = float(
                startup_text.strip()
            )

            startup_age_s = (
                now_s - startup_s
            )

            if (
                0.0
                <= startup_age_s
                <= STARTUP_GRACE_S
            ):
                print(
                    "STARTUP GRACE"
                )
                return 0

        except (
            OSError,
            ValueError,
        ):
            pass

    watchdog = ExternalWatchdog(
        HEARTBEAT_PATH,
        stale_after_s=2.0,
    )

    state = watchdog.evaluate(
        now_s
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