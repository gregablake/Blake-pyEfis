"""
Real Blake PFD engine/EMS serial input.

The engine controller sends one UTF-8 JSON object per line.

Example:
{
  "rpm": 2450,
  "volts": 13.9,
  "amps": 8.2,
  "oil_pressure_psi": 45.0,
  "oil_temp_f": 185.0,
  "fuel_pressure_psi": 4.8,
  "fuel_flow_gph": 6.5,
  "cht_f": [330, 325, 335, 328, 326, 332],
  "egt_f": [1325, 1310],
  "ignition_a": true,
  "ignition_b": true,
  "alternator_online": true,
  "starter_engaged": false
}

No successful parse means last_success_s is NOT refreshed.
"""

from __future__ import annotations

import json

from math import isfinite
from time import monotonic
from typing import Any, Callable

from pyefis.user.blake_pfd.engine_data import EngineData


class SerialEngineSourceError(RuntimeError):
    """Real engine serial data are currently unavailable."""


def _finite_number(
    payload: dict[str, Any],
    key: str,
) -> float:
    if key not in payload:
        raise SerialEngineSourceError(
            f"Missing engine field: {key}"
        )

    try:
        value = float(payload[key])
    except (TypeError, ValueError) as exc:
        raise SerialEngineSourceError(
            f"Invalid engine field: {key}"
        ) from exc

    if not isfinite(value):
        raise SerialEngineSourceError(
            f"Non-finite engine field: {key}"
        )

    return value


def _optional_number(
    payload: dict[str, Any],
    key: str,
    default: float = 0.0,
) -> float:
    if key not in payload:
        return default

    return _finite_number(
        payload,
        key,
    )


def _required_bool(
    payload: dict[str, Any],
    key: str,
) -> bool:
    if key not in payload:
        raise SerialEngineSourceError(
            f"Missing engine field: {key}"
        )

    value = payload[key]

    if type(value) is not bool:
        raise SerialEngineSourceError(
            f"Invalid engine boolean: {key}"
        )

    return value


def _temperature_list(
    payload: dict[str, Any],
    key: str,
    required_length: int,
) -> list[float]:
    values = payload.get(key)

    if not isinstance(values, list):
        raise SerialEngineSourceError(
            f"Invalid engine field: {key}"
        )

    if len(values) != required_length:
        raise SerialEngineSourceError(
            f"{key} must contain "
            f"{required_length} values"
        )

    result: list[float] = []

    for value in values:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise SerialEngineSourceError(
                f"Invalid value in {key}"
            ) from exc

        if not isfinite(numeric):
            raise SerialEngineSourceError(
                f"Non-finite value in {key}"
            )

        result.append(numeric)

    return result


def engine_data_from_payload(
    payload: Any,
) -> EngineData:
    if not isinstance(payload, dict):
        raise SerialEngineSourceError(
            "Engine serial payload must be a JSON object."
        )

    return EngineData(
        rpm=_finite_number(
            payload,
            "rpm",
        ),
        volts=_finite_number(
            payload,
            "volts",
        ),
        amps=_finite_number(
            payload,
            "amps",
        ),
        oil_pressure_psi=_finite_number(
            payload,
            "oil_pressure_psi",
        ),
        oil_temp_f=_finite_number(
            payload,
            "oil_temp_f",
        ),
        fuel_pressure_psi=_finite_number(
            payload,
            "fuel_pressure_psi",
        ),
        fuel_flow_gph=_finite_number(
            payload,
            "fuel_flow_gph",
        ),
        cht_f=_temperature_list(
            payload,
            "cht_f",
            6,
        ),
        egt_f=_temperature_list(
            payload,
            "egt_f",
            2,
        ),
        ignition_a=_required_bool(
            payload,
            "ignition_a",
        ),
        ignition_b=_required_bool(
            payload,
            "ignition_b",
        ),
        alternator_online=_required_bool(
            payload,
            "alternator_online",
        ),
        starter_engaged=_required_bool(
            payload,
            "starter_engaged",
        ),
        fuel_remaining_gal=_optional_number(
            payload,
            "fuel_remaining_gal",
        ),
        fuel_used_gal=_optional_number(
            payload,
            "fuel_used_gal",
        ),
        endurance_hr=_optional_number(
            payload,
            "endurance_hr",
        ),
        fuel_range_nm=_optional_number(
            payload,
            "fuel_range_nm",
        ),
    )


class SerialEngineSource:
    """
    Recoverable engine serial source.

    Serial connection is opened lazily so the PFD can boot with
    the engine controller disconnected.

    A read exception drops the connection so the next read attempts
    to reconnect automatically.
    """

    def __init__(
        self,
        port: str = "/dev/ttyACM0",
        baudrate: int = 115200,
        timeout_s: float = 0.05,
        serial_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.port = port
        self.baudrate = int(baudrate)
        self.timeout_s = float(timeout_s)

        self.last_success_s: float | None = None

        self._serial_factory = serial_factory
        self._serial = None

        self._next_reconnect_s = 0.0
        self._reconnect_backoff_s = 1.0

    def _connect(self) -> None:
        if self._serial is not None:
            return

        next_reconnect_s = getattr(
            self,
            "_next_reconnect_s",
            0.0,
        )

        now_s = None

        if next_reconnect_s > 0.0:
            now_s = monotonic()

            if now_s < next_reconnect_s:
                raise SerialEngineSourceError(
                    "Engine serial port unavailable."
                )

        factory = self._serial_factory

        if factory is None:
            try:
                import serial
            except ImportError as exc:
                raise SerialEngineSourceError(
                    "pyserial is not installed."
                ) from exc

            factory = serial.Serial

        try:
            connection = factory(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout_s,
            )

        except Exception as exc:
            self._serial = None

            if now_s is None:
                now_s = monotonic()

            self._next_reconnect_s = (
                now_s
                + getattr(
                    self,
                    "_reconnect_backoff_s",
                    1.0,
                )
            )

            raise SerialEngineSourceError(
                "Engine serial port unavailable."
            ) from exc

        self._serial = connection
        self._next_reconnect_s = 0.0

    def _disconnect(self) -> None:
        connection = self._serial
        self._serial = None

        if connection is None:
            return

        try:
            connection.close()
        except Exception:
            pass

    def read(self) -> EngineData:
        self._connect()

        connection = self._serial

        if connection is None:
            raise SerialEngineSourceError(
                "Engine serial port unavailable."
            )

        try:
            raw_line = connection.readline()
        except Exception as exc:
            # Force a reconnect on the next attempt.
            self._disconnect()

            raise SerialEngineSourceError(
                "Engine serial read failed."
            ) from exc

        if not raw_line:
            # Keep the established connection, but do not refresh
            # the freshness timestamp.
            raise SerialEngineSourceError(
                "No engine serial data received."
            )

        try:
            if isinstance(raw_line, bytes):
                line = raw_line.decode(
                    "utf-8",
                    errors="strict",
                )
            else:
                line = str(raw_line)

            payload = json.loads(
                line.strip()
            )

            engine = engine_data_from_payload(
                payload
            )

        except SerialEngineSourceError:
            raise
        except Exception as exc:
            raise SerialEngineSourceError(
                "Invalid engine serial message."
            ) from exc

        self.last_success_s = monotonic()

        return engine
