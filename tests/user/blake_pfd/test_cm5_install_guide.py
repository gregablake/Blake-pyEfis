from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GUIDE = REPO_ROOT / "CM5_INSTALL.md"


def test_cm5_install_guide_covers_required_first_boot_setup() -> None:
    assert GUIDE.exists()

    text = GUIDE.read_text(
        encoding="utf-8",
    )

    required = [
        "Raspberry Pi OS",
        "64-bit",
        "Trixie",
        "i2c-tools",
        "gpsd",
        "python3-venv",
        "dialout",
        "raspi-config",
        ".[qt,hardware]",
        ".config/blake-pfd/environment",
        "BLAKE_PFD_ENGINE_SERIAL_PORT=",
        "/dev/serial/by-id/",
        "blake-pfd.service",
        "blake-pfd-watchdog.service",
        "blake-pfd-watchdog.timer",
        "systemctl --user daemon-reload",
        "systemctl --user enable",
    ]

    for item in required:
        assert item in text
