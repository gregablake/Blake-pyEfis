from __future__ import annotations

from pyefis.user.blake_pfd.hardware_readers import (
    AirspeedReader,
    BaroReader,
    Bno085Reader,
)


class TransientBnoSensor:
    def __init__(self) -> None:
        self.quaternion_calls = 0

    @property
    def quaternion(self):
        self.quaternion_calls += 1

        if self.quaternion_calls == 1:
            raise OSError(
                "temporary BNO085 I2C failure"
            )

        # Identity quaternion.
        return (
            0.0,
            0.0,
            0.0,
            1.0,
        )

    @property
    def acceleration(self):
        return (
            0.0,
            0.0,
            9.80665,
        )


class TransientBaroSensor:
    def __init__(self) -> None:
        self.pressure_calls = 0

    @property
    def pressure(self):
        self.pressure_calls += 1

        if self.pressure_calls == 1:
            raise OSError(
                "temporary BMP388 I2C failure"
            )

        return 1013.25

    @property
    def temperature(self):
        return 20.0


class TransientAirspeedChannel:
    def __init__(self) -> None:
        self.voltage_calls = 0

    @property
    def voltage(self):
        self.voltage_calls += 1

        if self.voltage_calls == 1:
            raise OSError(
                "temporary ADS1115 I2C failure"
            )

        # 2.6 V with a 2.5 V zero and 1 V/kPa
        # corresponds to about 100 Pa differential.
        return 2.6


def test_bno085_recovers_after_transient_read_exception() -> None:
    sensor = TransientBnoSensor()

    reader = Bno085Reader.__new__(
        Bno085Reader
    )

    reader.ok = True
    reader.sensor = sensor
    reader.last_heading_deg = 0.0
    reader.last_yaw_deg = 0.0
    reader.last_update_s = 0.0
    reader.last_success_s = None

    first = reader.read()

    assert first["pitch_deg"] == 0.0
    assert reader.last_success_s is None

    second = reader.read()

    # The established sensor object must remain eligible
    # for another read after a transient bus exception.
    assert sensor.quaternion_calls == 2
    assert reader.ok is True
    assert reader.last_success_s is not None

    assert second["pitch_deg"] == 0.0
    assert second["roll_deg"] == 0.0
    assert second["accel_z_g"] == 1.0


def test_baro_recovers_after_transient_read_exception() -> None:
    sensor = TransientBaroSensor()

    reader = BaroReader.__new__(
        BaroReader
    )

    reader.ok = True
    reader.sensor = sensor
    reader.last_success_s = None

    first = reader.read()

    assert first["static_pressure_pa"] == 101325.0
    assert reader.last_success_s is None

    second = reader.read()

    assert sensor.pressure_calls == 2
    assert reader.ok is True
    assert reader.last_success_s is not None

    assert (
        second["static_pressure_pa"]
        == 101325.0
    )
    assert (
        second["outside_air_temp_c"]
        == 20.0
    )


def test_airspeed_recovers_after_transient_read_exception() -> None:
    channel = TransientAirspeedChannel()

    reader = AirspeedReader.__new__(
        AirspeedReader
    )

    reader.ok = True
    reader.ads = object()
    reader.channel = channel
    reader.last_success_s = None

    reader.sensor_supply_v = 5.0
    reader.zero_pressure_v = 2.5
    reader.volts_per_kpa = 1.0

    first = reader.read()

    assert (
        first["differential_pressure_pa"]
        == 0.0
    )
    assert reader.last_success_s is None

    second = reader.read()

    assert channel.voltage_calls == 2
    assert reader.ok is True
    assert reader.last_success_s is not None

    assert abs(
        second["differential_pressure_pa"]
        - 100.0
    ) < 1e-9
