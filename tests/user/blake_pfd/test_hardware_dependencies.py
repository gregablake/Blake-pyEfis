from pathlib import Path
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_cm5_hardware_dependencies_are_declared() -> None:
    pyproject = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(
            encoding="utf-8",
        )
    )

    hardware = (
        pyproject["project"]
        ["optional-dependencies"]
        ["hardware"]
    )

    normalized = {
        requirement.split(">=")[0]
        .split("==")[0]
        .lower()
        for requirement in hardware
    }

    assert "adafruit-blinka" in normalized
    assert "adafruit-circuitpython-bno08x" in normalized
    assert "adafruit-circuitpython-bmp3xx" in normalized
    assert "adafruit-circuitpython-ads1x15" in normalized
