from __future__ import annotations

import json

import pytest

from pyefis.user.blake_pfd.core.baro_setting_store import (
    BaroSettingStore,
)


def test_missing_state_uses_configured_default(
    tmp_path,
):
    store = BaroSettingStore(
        tmp_path / "baro.json"
    )

    assert (
        store.load(
            default_inhg=29.92
        )
        == pytest.approx(29.92)
    )


def test_saved_setting_round_trips(
    tmp_path,
):
    path = tmp_path / "baro.json"

    store = BaroSettingStore(path)

    store.save(30.17)

    assert path.exists()

    assert (
        store.load(
            default_inhg=29.92
        )
        == pytest.approx(30.17)
    )


def test_save_creates_parent_directory(
    tmp_path,
):
    path = (
        tmp_path
        / "state"
        / "blake_pyefis"
        / "baro.json"
    )

    store = BaroSettingStore(path)

    store.save(30.01)

    assert path.exists()


@pytest.mark.parametrize(
    "bad_contents",
    [
        "",
        "not json",
        "[]",
        "{}",
        '{"baro_setting_inhg": null}',
        '{"baro_setting_inhg": "nan"}',
        '{"baro_setting_inhg": "inf"}',
        '{"baro_setting_inhg": 27.49}',
        '{"baro_setting_inhg": 31.51}',
        '{"baro_setting_inhg": 30.123}',
    ],
)
def test_corrupt_or_invalid_state_uses_default(
    tmp_path,
    bad_contents,
):
    path = tmp_path / "baro.json"

    path.write_text(
        bad_contents,
        encoding="utf-8",
    )

    store = BaroSettingStore(path)

    assert (
        store.load(
            default_inhg=29.92
        )
        == pytest.approx(29.92)
    )


@pytest.mark.parametrize(
    "bad_value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        27.49,
        31.51,
        30.123,
    ],
)
def test_invalid_save_is_rejected(
    tmp_path,
    bad_value,
):
    path = tmp_path / "baro.json"

    store = BaroSettingStore(path)

    with pytest.raises(ValueError):
        store.save(bad_value)

    assert not path.exists()


def test_failed_invalid_save_preserves_existing_state(
    tmp_path,
):
    path = tmp_path / "baro.json"

    store = BaroSettingStore(path)

    store.save(30.12)

    with pytest.raises(ValueError):
        store.save(float("nan"))

    assert (
        store.load(
            default_inhg=29.92
        )
        == pytest.approx(30.12)
    )


def test_state_file_has_explicit_version(
    tmp_path,
):
    path = tmp_path / "baro.json"

    store = BaroSettingStore(path)

    store.save(29.84)

    raw = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert raw == {
        "version": 1,
        "baro_setting_inhg": 29.84,
    }


def test_unknown_state_version_uses_default(
    tmp_path,
):
    path = tmp_path / "baro.json"

    path.write_text(
        json.dumps(
            {
                "version": 999,
                "baro_setting_inhg": 30.12,
            }
        ),
        encoding="utf-8",
    )

    store = BaroSettingStore(path)

    assert (
        store.load(
            default_inhg=29.92
        )
        == pytest.approx(29.92)
    )
