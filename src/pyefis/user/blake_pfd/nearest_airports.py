from __future__ import annotations

import argparse

from pyefis.user.blake_pfd.database_importer import AviationDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Find nearest airports")
    parser.add_argument("--lat", type=float, required=True, help="Aircraft latitude")
    parser.add_argument("--lon", type=float, required=True, help="Aircraft longitude")
    parser.add_argument("--count", type=int, default=10, help="Number of results")

    args = parser.parse_args()

    db = AviationDatabase()
    db.load_all()

    nearest = db.nearest_airports(
        args.lat,
        args.lon,
        max_results=args.count,
    )

    print()
    print(f"Nearest airports to {args.lat:.4f}, {args.lon:.4f}")
    print("-" * 70)

    for distance_nm, airport in nearest:
        print(
            f"{airport.ident:<6} "
            f"{distance_nm:>6.1f} NM  "
            f"{airport.type:<15} "
            f"{airport.name}"
        )

    print()


if __name__ == "__main__":
    main()