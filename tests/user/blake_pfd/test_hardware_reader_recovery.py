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


class DeadBnoSensor:
    @property
    def quaternion(self):
        raise OSError(
            "persistent BNO085 I2C failure"
        )

    @property
    def acceleration(self):
        raise OSError(
            "persistent BNO085 I2C failure"
        )


class DeadBaroSensor:
    @property
    def pressure(self):
        raise OSError(
            "persistent BMP388 I2C failure"
        )

    @property
    def temperature(self):
        raise OSError(
            "persistent BMP388 I2C failure"
        )


class DeadAirspeedChannel:
    @property
    def voltage(self):
        raise OSError(
            "persistent ADS1115 I2C failure"
        )


def test_bno085_releases_dead_sensor_after_repeated_failures() -> None:
    reader = Bno085Reader.__new__(
        Bno085Reader
    )

    reader.ok = True
    reader.sensor = DeadBnoSensor()
    reader.last_heading_deg = 0.0
    reader.last_yaw_deg = 0.0
    reader.last_update_s = 0.0
    reader.last_success_s = 10.0

    reader.read()
    reader.read()
    reader.read()

    # After repeated failures the dead hardware object should be
    # released so a later read can perform true reinitialization.
    assert reader.sensor is None

    # Failed samples must never make old data fresh.
    assert reader.last_success_s == 10.0


def test_baro_releases_dead_sensor_after_repeated_failures() -> None:
    reader = BaroReader.__new__(
        BaroReader
    )

    reader.ok = True
    reader.sensor = DeadBaroSensor()
    reader.last_success_s = 20.0

    reader.read()
    reader.read()
    reader.read()

    assert reader.sensor is None
    assert reader.last_success_s == 20.0


def test_airspeed_releases_dead_channel_after_repeated_failures() -> None:
    reader = AirspeedReader.__new__(
        AirspeedReader
    )

    reader.ok = True
    reader.ads = object()
    reader.channel = DeadAirspeedChannel()
    reader.last_success_s = 30.0

    reader.sensor_supply_v = 5.0
    reader.zero_pressure_v = 2.5
    reader.volts_per_kpa = 1.0

    reader.read()
    reader.read()
    reader.read()

    assert reader.channel is None
    assert reader.last_success_s == 30.0


class HealthyBnoSensor:
    @property
    def quaternion(self):
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


class HealthyBaroSensor:
    @property
    def pressure(self):
        return 1013.25

    @property
    def temperature(self):
        return 22.0


class HealthyAirspeedChannel:
    @property
    def voltage(self):
        return 2.6


def test_bno085_reinitializes_after_dead_sensor_release() -> None:
    reader = Bno085Reader.__new__(
        Bno085Reader
    )

    reader.ok = True
    reader.sensor = DeadBnoSensor()
    reader.last_heading_deg = 0.0
    reader.last_yaw_deg = 0.0
    reader.last_update_s = 0.0
    reader.last_success_s = 10.0
    reader._consecutive_failures = 0

    reader.read()
    reader.read()
    reader.read()

    assert reader.sensor is None
    assert reader.ok is False

    replacement = HealthyBnoSensor()
    initialize_calls = []

    def initialize():
        initialize_calls.append(True)
        reader.sensor = replacement
        reader.ok = True
        reader._consecutive_failures = 0
        return True

    reader._initialize_hardware = initialize

    recovered = reader.read()

    assert len(initialize_calls) == 1
    assert reader.sensor is replacement
    assert reader.ok is True
    assert reader.last_success_s is not None
    assert recovered["pitch_deg"] == 0.0
    assert recovered["roll_deg"] == 0.0
    assert recovered["accel_z_g"] == 1.0


def test_baro_reinitializes_after_dead_sensor_release() -> None:
    reader = BaroReader.__new__(
        BaroReader
    )

    reader.ok = True
    reader.sensor = DeadBaroSensor()
    reader.last_success_s = 20.0
    reader._consecutive_failures = 0

    reader.read()
    reader.read()
    reader.read()

    assert reader.sensor is None
    assert reader.ok is False

    replacement = HealthyBaroSensor()
    initialize_calls = []

    def initialize():
        initialize_calls.append(True)
        reader.sensor = replacement
        reader.ok = True
        reader._consecutive_failures = 0
        return True

    reader._initialize_hardware = initialize

    recovered = reader.read()

    assert len(initialize_calls) == 1
    assert reader.sensor is replacement
    assert reader.ok is True
    assert reader.last_success_s is not None
    assert recovered["static_pressure_pa"] == 101325.0
    assert recovered["outside_air_temp_c"] == 22.0


def test_airspeed_reinitializes_after_dead_channel_release() -> None:
    reader = AirspeedReader.__new__(
        AirspeedReader
    )

    reader.ok = True
    reader.ads = object()
    reader.channel = DeadAirspeedChannel()
    reader.last_success_s = 30.0
    reader._consecutive_failures = 0

    reader.sensor_supply_v = 5.0
    reader.zero_pressure_v = 2.5
    reader.volts_per_kpa = 1.0

    reader.read()
    reader.read()
    reader.read()

    assert reader.channel is None
    assert reader.ok is False

    replacement = HealthyAirspeedChannel()
    replacement_ads = object()
    initialize_calls = []

    def initialize():
        initialize_calls.append(True)
        reader.ads = replacement_ads
        reader.channel = replacement
        reader.ok = True
        reader._consecutive_failures = 0
        return True

    reader._initialize_hardware = initialize

    recovered = reader.read()

    assert len(initialize_calls) == 1
    assert reader.ads is replacement_ads
    assert reader.channel is replacement
    assert reader.ok is True
    assert reader.last_success_s is not None
    assert abs(
        recovered["differential_pressure_pa"]
        - 100.0
    ) < 1e-9


def test_bno085_yaw_rate_uses_interval_between_samples(
    monkeypatch,
) -> None:
    import math

    import pyefis.user.blake_pfd.hardware_readers as hw

    class SequentialYawSensor:
        def __init__(self) -> None:
            self.yaws = iter(
                (
                    10.0,
                    20.0,
                )
            )

        @property
        def quaternion(self):
            yaw_deg = next(self.yaws)
            half_yaw_rad = math.radians(
                yaw_deg
            ) / 2.0

            return (
                0.0,
                0.0,
                math.sin(half_yaw_rad),
                math.cos(half_yaw_rad),
            )

        @property
        def acceleration(self):
            return (
                0.0,
                0.0,
                9.80665,
            )

    times = iter(
        (
            1.0,
            2.0,
        )
    )

    monkeypatch.setattr(
        hw,
        "monotonic",
        lambda: next(times),
    )

    reader = Bno085Reader.__new__(
        Bno085Reader
    )

    reader.ok = True
    reader.sensor = SequentialYawSensor()
    reader.last_heading_deg = 0.0
    reader.last_yaw_deg = 0.0
    reader.last_update_s = 0.0
    reader.last_success_s = 0.0
    reader._consecutive_failures = 0
    reader._has_yaw_sample = True

    first = reader.read()
    second = reader.read()

    # 10 degrees of yaw change occurred during each
    # one-second sample interval.
    assert abs(
        first["yaw_rate_deg_s"] - 10.0
    ) < 1e-9

    assert abs(
        second["yaw_rate_deg_s"] - 10.0
    ) < 1e-9

    # The reader must advance its rate-calculation clock
    # after every successful AHRS sample.
    assert reader.last_update_s == 2.0


def test_bno085_first_valid_sample_has_zero_yaw_rate(
    monkeypatch,
) -> None:
    import math

    import pyefis.user.blake_pfd.hardware_readers as hw

    class InitialYawSensor:
        @property
        def quaternion(self):
            yaw_deg = 90.0
            half_yaw_rad = math.radians(
                yaw_deg
            ) / 2.0

            return (
                0.0,
                0.0,
                math.sin(half_yaw_rad),
                math.cos(half_yaw_rad),
            )

        @property
        def acceleration(self):
            return (
                0.0,
                0.0,
                9.80665,
            )

    monkeypatch.setattr(
        hw,
        "monotonic",
        lambda: 10.0,
    )

    reader = Bno085Reader.__new__(
        Bno085Reader
    )

    reader.ok = True
    reader.sensor = InitialYawSensor()
    reader.last_heading_deg = 0.0
    reader.last_yaw_deg = 0.0
    reader.last_update_s = 0.0
    reader.last_success_s = None
    reader._consecutive_failures = 0

    sample = reader.read()

    # There is no previous real AHRS sample yet, so the
    # first valid attitude must not generate an artificial
    # turn rate from the default zero-degree heading.
    assert abs(
        sample["heading_deg"] - 90.0
    ) < 1e-9

    assert sample["yaw_rate_deg_s"] == 0.0


def test_bno085_waits_for_reconnect_backoff(
    monkeypatch,
) -> None:
    import pyefis.user.blake_pfd.hardware_readers as hw

    clock = {
        "now": 5.0,
    }

    monkeypatch.setattr(
        hw,
        "monotonic",
        lambda: clock["now"],
    )

    reader = Bno085Reader.__new__(
        Bno085Reader
    )

    reader.ok = False
    reader.sensor = None
    reader.last_heading_deg = 0.0
    reader.last_yaw_deg = 0.0
    reader.last_update_s = 0.0
    reader.last_success_s = None
    reader._consecutive_failures = 0
    reader._has_yaw_sample = False

    # Hardware must not be retried before this time.
    reader._next_reconnect_s = 10.0

    initialize_calls = []

    def initialize():
        initialize_calls.append(
            clock["now"]
        )
        return False

    reader._initialize_hardware = initialize

    # Multiple PFD reads before the reconnect deadline must
    # return fallback data without hammering the I2C bus.
    reader.read()
    reader.read()
    reader.read()

    assert initialize_calls == []

    # Once the reconnect deadline arrives, exactly one hardware
    # initialization attempt is allowed.
    clock["now"] = 10.0

    reader.read()

    assert initialize_calls == [
        10.0,
    ]


def test_baro_waits_for_reconnect_backoff(
    monkeypatch,
) -> None:
    import pyefis.user.blake_pfd.hardware_readers as hw

    clock = {
        "now": 5.0,
    }

    monkeypatch.setattr(
        hw,
        "monotonic",
        lambda: clock["now"],
    )

    reader = BaroReader.__new__(
        BaroReader
    )

    reader.ok = False
    reader.sensor = None
    reader.last_success_s = None
    reader._consecutive_failures = 0

    reader._next_reconnect_s = 10.0

    initialize_calls = []

    def initialize():
        initialize_calls.append(
            clock["now"]
        )
        return False

    reader._initialize_hardware = initialize

    reader.read()
    reader.read()
    reader.read()

    assert initialize_calls == []

    clock["now"] = 10.0

    reader.read()

    assert initialize_calls == [
        10.0,
    ]


def test_airspeed_waits_for_reconnect_backoff(
    monkeypatch,
) -> None:
    import pyefis.user.blake_pfd.hardware_readers as hw

    clock = {
        "now": 5.0,
    }

    monkeypatch.setattr(
        hw,
        "monotonic",
        lambda: clock["now"],
    )

    reader = AirspeedReader.__new__(
        AirspeedReader
    )

    reader.ok = False
    reader.ads = None
    reader.channel = None
    reader.last_success_s = None
    reader._consecutive_failures = 0

    reader.sensor_supply_v = 5.0
    reader.zero_pressure_v = 2.5
    reader.volts_per_kpa = 1.0

    reader._next_reconnect_s = 10.0

    initialize_calls = []

    def initialize():
        initialize_calls.append(
            clock["now"]
        )
        return False

    reader._initialize_hardware = initialize

    reader.read()
    reader.read()
    reader.read()

    assert initialize_calls == []

    clock["now"] = 10.0

    reader.read()

    assert initialize_calls == [
        10.0,
    ]
