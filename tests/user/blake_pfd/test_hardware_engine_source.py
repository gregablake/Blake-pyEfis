from __future__ import annotations

import json

from unittest.mock import patch

import pytest

from pyefis.user.blake_pfd.core.sensor_manager import (
    SensorManager,
    SensorMode,
    UnavailableEngineSource,
)
from pyefis.user.blake_pfd.flight_computer import FlightComputer
from pyefis.user.blake_pfd.hardware_engine import (
    SerialEngineSource,
    SerialEngineSourceError,
)


def valid_engine_payload() -> dict:
    return {
        "rpm": 2450.0,
        "volts": 13.9,
        "amps": 8.2,
        "oil_pressure_psi": 45.0,
        "oil_temp_f": 185.0,
        "fuel_pressure_psi": 4.8,
        "fuel_flow_gph": 6.5,
        "cht_f": [
            330.0,
            325.0,
            335.0,
            328.0,
            326.0,
            332.0,
        ],
        "egt_f": [
            1325.0,
            1310.0,
        ],
        "ignition_a": True,
        "ignition_b": True,
        "alternator_online": True,
        "starter_engaged": False,
    }


def encoded_payload(
    payload: dict,
) -> bytes:
    return (
        json.dumps(payload)
        + "\n"
    ).encode("utf-8")


class FakeSerial:
    def __init__(
        self,
        lines=None,
        *,
        read_exception=None,
    ) -> None:
        self.lines = list(
            lines or []
        )
        self.read_exception = read_exception
        self.closed = False

    def readline(self):
        if self.read_exception is not None:
            exc = self.read_exception
            self.read_exception = None
            raise exc

        if not self.lines:
            return b""

        return self.lines.pop(0)

    def close(self) -> None:
        self.closed = True


def test_hardware_mode_has_real_engine_source() -> None:
    manager = SensorManager(
        flight_computer=FlightComputer(),
        use_hardware=True,
    )

    assert manager.mode is SensorMode.HARDWARE

    assert not isinstance(
        manager.engine_source,
        UnavailableEngineSource,
    )

    assert isinstance(
        manager.engine_source,
        SerialEngineSource,
    )

    assert hasattr(
        manager.engine_source,
        "last_success_s",
    )


def test_valid_serial_message_creates_engine_data() -> None:
    fake_serial = FakeSerial(
        [
            encoded_payload(
                valid_engine_payload()
            )
        ]
    )

    def factory(**kwargs):
        return fake_serial

    source = SerialEngineSource(
        serial_factory=factory,
    )

    with patch(
        "pyefis.user.blake_pfd.hardware_engine.monotonic",
        return_value=50.0,
    ):
        engine = source.read()

    assert engine.rpm == 2450.0
    assert engine.volts == 13.9
    assert engine.amps == 8.2

    assert engine.oil_pressure_psi == 45.0
    assert engine.oil_temp_f == 185.0
    assert engine.fuel_pressure_psi == 4.8
    assert engine.fuel_flow_gph == 6.5

    assert engine.cht_f == [
        330.0,
        325.0,
        335.0,
        328.0,
        326.0,
        332.0,
    ]

    assert engine.egt_f == [
        1325.0,
        1310.0,
    ]

    assert engine.ignition_a is True
    assert engine.ignition_b is True
    assert engine.alternator_online is True
    assert engine.starter_engaged is False

    assert source.last_success_s == 50.0


def test_malformed_json_does_not_refresh_engine_freshness() -> None:
    fake_serial = FakeSerial(
        [
            b"{this is not valid json}\n",
        ]
    )

    source = SerialEngineSource(
        serial_factory=lambda **kwargs: fake_serial,
    )

    source.last_success_s = 25.0

    with patch(
        "pyefis.user.blake_pfd.hardware_engine.monotonic"
    ) as monotonic_mock:
        with pytest.raises(
            SerialEngineSourceError,
            match="Invalid engine serial message",
        ):
            source.read()

    assert source.last_success_s == 25.0
    monotonic_mock.assert_not_called()


def test_missing_required_engine_field_does_not_refresh() -> None:
    payload = valid_engine_payload()
    del payload["oil_pressure_psi"]

    fake_serial = FakeSerial(
        [
            encoded_payload(payload),
        ]
    )

    source = SerialEngineSource(
        serial_factory=lambda **kwargs: fake_serial,
    )

    source.last_success_s = 30.0

    with pytest.raises(
        SerialEngineSourceError,
        match="Missing engine field: oil_pressure_psi",
    ):
        source.read()

    assert source.last_success_s == 30.0


def test_serial_read_failure_disconnects_and_recovers() -> None:
    first_serial = FakeSerial(
        read_exception=OSError(
            "temporary USB serial failure"
        ),
    )

    second_serial = FakeSerial(
        [
            encoded_payload(
                valid_engine_payload()
            ),
        ]
    )

    connections = [
        first_serial,
        second_serial,
    ]

    factory_calls = []

    def factory(**kwargs):
        factory_calls.append(kwargs)
        return connections.pop(0)

    source = SerialEngineSource(
        port="/dev/ttyACM0",
        baudrate=115200,
        timeout_s=0.05,
        serial_factory=factory,
    )

    with pytest.raises(
        SerialEngineSourceError,
        match="Engine serial read failed",
    ):
        source.read()

    assert first_serial.closed is True
    assert source._serial is None
    assert source.last_success_s is None

    with patch(
        "pyefis.user.blake_pfd.hardware_engine.monotonic",
        return_value=75.0,
    ):
        engine = source.read()

    assert len(factory_calls) == 2
    assert engine.rpm == 2450.0
    assert source.last_success_s == 75.0
    assert source._serial is second_serial


def test_empty_serial_read_does_not_refresh_freshness() -> None:
    fake_serial = FakeSerial()

    source = SerialEngineSource(
        serial_factory=lambda **kwargs: fake_serial,
    )

    source.last_success_s = 40.0

    with pytest.raises(
        SerialEngineSourceError,
        match="No engine serial data received",
    ):
        source.read()

    assert source.last_success_s == 40.0

    # A timeout/empty read alone should not throw away an otherwise
    # established serial connection.
    assert source._serial is fake_serial
    assert fake_serial.closed is False
