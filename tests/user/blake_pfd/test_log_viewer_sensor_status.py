from __future__ import annotations

import csv

from pyefis.user.blake_pfd.log_viewer import summarize_log


def write_log(path, fieldnames, rows) -> None:
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file_handle:
        writer = csv.DictWriter(
            file_handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def test_invalid_cht_sample_is_excluded_from_summary(
    tmp_path,
    capsys,
) -> None:
    path = tmp_path / "flight_log_test.csv"

    write_log(
        path,
        [
            "timestamp_utc",
            "engine_cht_1",
            "engine_cht_1_valid",
            "engine_cht_1_fresh",
        ],
        [
            {
                "timestamp_utc": "2026-08-26T12:00:00+00:00",
                "engine_cht_1": "350.0",
                "engine_cht_1_valid": "True",
                "engine_cht_1_fresh": "True",
            },
            {
                "timestamp_utc": "2026-08-26T12:00:01+00:00",
                "engine_cht_1": "700.0",
                "engine_cht_1_valid": "False",
                "engine_cht_1_fresh": "False",
            },
        ],
    )

    summarize_log(path)

    output = capsys.readouterr().out

    assert "CHT max: 350 °F" in output
    assert "CHT1 max: 350 °F" in output
    assert "700" not in output


def test_stale_oil_pressure_sample_is_excluded_from_summary(
    tmp_path,
    capsys,
) -> None:
    path = tmp_path / "flight_log_test.csv"

    write_log(
        path,
        [
            "timestamp_utc",
            "engine_oil_pressure_psi",
            "engine_oil_pressure_psi_valid",
            "engine_oil_pressure_psi_fresh",
        ],
        [
            {
                "timestamp_utc": "2026-08-26T12:00:00+00:00",
                "engine_oil_pressure_psi": "45.0",
                "engine_oil_pressure_psi_valid": "True",
                "engine_oil_pressure_psi_fresh": "True",
            },
            {
                "timestamp_utc": "2026-08-26T12:00:01+00:00",
                "engine_oil_pressure_psi": "-5.0",
                "engine_oil_pressure_psi_valid": "True",
                "engine_oil_pressure_psi_fresh": "False",
            },
        ],
    )

    summarize_log(path)

    output = capsys.readouterr().out

    assert "Oil PSI min/max: 45 / 45" in output
    assert "-5" not in output


def test_legacy_log_without_status_columns_still_works(
    tmp_path,
    capsys,
) -> None:
    path = tmp_path / "flight_log_legacy.csv"

    write_log(
        path,
        [
            "timestamp_utc",
            "engine_rpm",
            "engine_cht_1",
        ],
        [
            {
                "timestamp_utc": "2026-08-26T12:00:00+00:00",
                "engine_rpm": "2450.0",
                "engine_cht_1": "350.0",
            },
        ],
    )

    summarize_log(path)

    output = capsys.readouterr().out

    assert "RPM max: 2450" in output
    assert "CHT max: 350 °F" in output
    assert "CHT1 max: 350 °F" in output


def test_unknown_blank_status_is_not_treated_as_valid(
    tmp_path,
    capsys,
) -> None:
    path = tmp_path / "flight_log_unknown.csv"

    write_log(
        path,
        [
            "timestamp_utc",
            "engine_rpm",
            "engine_rpm_valid",
            "engine_rpm_fresh",
        ],
        [
            {
                "timestamp_utc": "2026-08-26T12:00:00+00:00",
                "engine_rpm": "9000.0",
                "engine_rpm_valid": "",
                "engine_rpm_fresh": "",
            },
        ],
    )

    summarize_log(path)

    output = capsys.readouterr().out

    assert "RPM max:" not in output
    assert "9000" not in output
