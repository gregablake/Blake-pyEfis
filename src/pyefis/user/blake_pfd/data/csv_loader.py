"""Utility helpers for loading CSV data files in the Blake PFD data package."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

DATA_DIR = Path(__file__).resolve().parent


def get_data_file_path(filename: str | Path) -> Path:
    """Return an absolute path for a data file by name or path.

    If the filename is already an existing path, that path is returned.
    Otherwise the file is resolved relative to the Blake PFD data directory.
    """
    return CSVDataLoader().resolve_path(filename)


def load_csv_rows(filename: str | Path, delimiter: str = ",", encoding: str = "utf-8") -> list[dict[str, str]]:
    """Load CSV rows as a list of dictionaries.

    The first row of the CSV file is interpreted as the header row.
    """
    return CSVDataLoader().load_rows(filename, delimiter=delimiter, encoding=encoding)


def load_csv_data(filename: str | Path, delimiter: str = ",", encoding: str = "utf-8") -> list[list[str]]:
    """Load CSV file as a list of rows (including header row)."""
    return CSVDataLoader().load_data(filename, delimiter=delimiter, encoding=encoding)


class CSVDataLoader:
    """Load CSV files from the Blake PFD data directory or an explicit path."""

    def __init__(self, data_dir: str | Path = DATA_DIR) -> None:
        self.data_dir = Path(data_dir).resolve()

    def resolve_path(self, filename: str | Path) -> Path:
        path = Path(filename)
        if path.is_absolute() or path.exists():
            return path.resolve()

        # Try the requested filename relative to the Blake PFD data directory.
        candidate = self.data_dir / path
        if candidate.exists():
            return candidate.resolve()

        # If no extension was provided, try adding .csv.
        if not candidate.suffix.lower() and not path.suffix.lower():
            csv_candidate = candidate.with_suffix(".csv")
            if csv_candidate.exists():
                return csv_candidate.resolve()

        raise FileNotFoundError(
            f"CSV file not found in data directory or path: {filename}"
        )

    def load_rows(
        self,
        filename: str | Path,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> list[dict[str, str]]:
        path = self.resolve_path(filename)
        with path.open(newline="", encoding=encoding) as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            return [row for row in reader]

    def load_data(
        self,
        filename: str | Path,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> list[list[str]]:
        path = self.resolve_path(filename)
        with path.open(newline="", encoding=encoding) as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            return [list(row) for row in reader]
