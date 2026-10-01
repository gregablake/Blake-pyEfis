# Blake PFD — Raspberry Pi CM5 Installation

## Target platform

Use Raspberry Pi OS Desktop, 64-bit, based on Trixie, on the Raspberry Pi Compute Module 5.

The repository is expected at:

    ~/Blake-pyEfis

This guide is for the Blake PFD hardware build rather than the older snap-based installation.

## 1. Update the CM5

    sudo apt update
    sudo apt full-upgrade -y

## 2. Install operating-system packages

    sudo apt install -y git python3 python3-pip python3-venv python3-dev build-essential i2c-tools gpsd gpsd-clients python3-gps

The GPS reader uses gpsd and the Debian python3-gps binding.

## 3. Enable I2C

Run:

    sudo raspi-config

Choose Interface Options, then I2C, then enable it.

After reboot, verify the bus with:

    ls -l /dev/i2c-*
    sudo i2cdetect -y 1

## 4. Serial permissions

Add the current user to dialout:

    sudo usermod -a -G dialout "$USER"

Reboot before continuing.

## 5. Clone the project

    cd "$HOME"
    git clone --branch efis-v2-refactor https://github.com/gregablake/Blake-pyEfis.git Blake-pyEfis
    cd "$HOME/Blake-pyEfis"

## 6. Create the virtual environment

Because python3-gps is supplied by the operating system, create the virtual environment with system packages visible:

    python3 -m venv --system-site-packages .venv
    source .venv/bin/activate

## 7. Install Blake PFD

Install Qt and the declared hardware dependencies:

    python -m pip install -e ".[qt,hardware]"

The hardware extra provides the Raspberry Pi Blinka and Adafruit BNO08x, BMP3XX, and ADS1x15 libraries.

## 8. Engine serial configuration

Do not permanently rely on /dev/ttyACM0.

Identify the stable EMS device using:

    ls -l /dev/serial/by-id/

Create:

    ~/.config/blake-pfd/environment

The file should contain:

    BLAKE_PFD_ENGINE_SERIAL_PORT=/dev/serial/by-id/REPLACE_WITH_ACTUAL_EMS_DEVICE

The exact /dev/serial/by-id/ path must be confirmed with the real EMS controller connected.

## 9. Install Blake PFD services

Create the user systemd directory:

    mkdir -p "$HOME/.config/systemd/user"

Copy:

    extras/extras/blake-pfd.service
    extras/extras/blake-pfd-watchdog.service
    extras/extras/blake-pfd-watchdog.timer

into:

    ~/.config/systemd/user/

Then run:

    systemctl --user daemon-reload
    systemctl --user enable blake-pfd.service blake-pfd-watchdog.timer

The watchdog timer runs blake-pfd-watchdog.service.

## 10. First hardware-mode test

Initially leave the aircraft sensors disconnected and launch manually:

    cd "$HOME/Blake-pyEfis"
    source .venv/bin/activate
    python -m pyefis.user.blake_pfd.pfd_demo --hardware

The application should remain running and fail closed when hardware is unavailable.

## 11. Connect sensors one at a time

Recommended bench order:

1. BNO085
2. BMP388
3. ADS1115
4. MPXV7002DP through ADS1115
5. GPS
6. EMS serial controller

After each device is connected, verify operation before adding the next one.

Do not connect the MPXV7002DP analog output directly to a CM5 GPIO input.

## 12. Bench validation

Test sensor disconnect and reconnect behavior, stale-data handling, reboot recovery, watchdog recovery, cold starts, warm starts, and extended operation.

Successful software tests and CM5 bench tests do not establish flightworthiness. Final aircraft installation still requires independent pitot/static calibration, AHRS orientation and heading validation, engine-sender calibration, electrical-noise testing, thermal testing, ground testing, and comparison against independent instruments.
