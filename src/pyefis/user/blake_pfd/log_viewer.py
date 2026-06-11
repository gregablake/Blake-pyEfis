from __future__ import annotations

import argparse
import csv
from pathlib import Path


LOG_DIR = Path(__file__).parent / "logs"


def list_logs() -> None:
    LOG_DIR.mkdir(exist_ok=True)

    logs = sorted(LOG_DIR.glob("flight_log_*.csv"))

    print()
    print("Available flight logs:")
    print("-" * 60)

    if not logs:
        print("No logs found.")
        print()
        return

    for index, log in enumerate(logs, start=1):
        print(f"{index:>2}. {log.name}")

    print()


def summarize_log(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("Log is empty.")
        return

    def values(field: str) -> list[float]:
        result = []
        for row in rows:
            try:
                result.append(float(row.get(field, 0.0)))
            except ValueError:
                pass
        return result

    ias = values("ias_kt")
    alt = values("pressure_alt_ft")
    gs = values("ground_speed_kt")

    print()
    print(f"Log: {path.name}")
    print("-" * 60)
    print(f"Rows: {len(rows)}")
    print(f"Start: {rows[0].get('timestamp_utc', '')}")
    print(f"End:   {rows[-1].get('timestamp_utc', '')}")

    if ias:
        print(f"IAS max: {max(ias):.0f} kt")
    if alt:
        print(f"ALT min/max: {min(alt):.0f} / {max(alt):.0f} ft")
    if gs:
        print(f"GS max: {max(gs):.0f} kt")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="View Blake PFD flight logs")
    parser.add_argument("--list", action="store_true", help="List available logs")
    parser.add_argument("--summary", help="Show summary for a log filename")

    args = parser.parse_args()

    if args.list:
        list_logs()
        return

    if args.summary:
        summarize_log(LOG_DIR / args.summary)
        return

    list_logs()


if __name__ == "__main__":
    main()