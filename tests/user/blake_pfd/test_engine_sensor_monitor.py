from __future__ import annotations

from math import nan

from pyefis.user.blake_pfd.core.engine_sensor_monitor import (
    EngineSensorMonitor,
)
from pyefis.user.blake_pfd.engine_data import EngineData


def test_engine_sensor_monitor_marks_fresh_finite_data_healthy() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            rpm=2450.0,
            volts=13.9,
            amps=8.0,
            oil_pressure_psi=45.0,
            oil_temp_f=190.0,
            fuel_pressure_psi=4.8,
            fuel_flow_gph=6.5,
            cht_f=[325.0] * 6,
            egt_f=[1325.0] * 2,
        ),
        source_fresh=True,
    )

    assert result.rpm.valid is True
    assert result.rpm.fresh is True
    assert result.oil_pressure.valid is True
    assert all(channel.valid for channel in result.cht)
    assert all(channel.fresh for channel in result.egt)


def test_engine_sensor_monitor_marks_source_stale() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            rpm=2450.0,
        ),
        source_fresh=False,
    )

    assert result.rpm.valid is True
    assert result.rpm.fresh is False
    assert result.rpm.message == "DATA STALE"


def test_engine_sensor_monitor_rejects_nonfinite_channel() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            oil_pressure_psi=nan,
        ),
        source_fresh=True,
    )

    assert result.oil_pressure.valid is False
    assert result.oil_pressure.fresh is False
    assert (
        result.oil_pressure.message
        == "INVALID DATA"
    )
    
def test_engine_sensor_monitor_rejects_implausible_rpm() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            rpm=9000.0,
        ),
        source_fresh=True,
    )

    assert result.rpm.valid is False
    assert result.rpm.fresh is False
    assert result.rpm.message == "IMPLAUSIBLE DATA"


def test_engine_sensor_monitor_rejects_implausible_oil_pressure() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            oil_pressure_psi=-5.0,
        ),
        source_fresh=True,
    )

    assert result.oil_pressure.valid is False
    assert result.oil_pressure.fresh is False
    assert (
        result.oil_pressure.message
        == "IMPLAUSIBLE DATA"
    )
    
def test_engine_sensor_monitor_rejects_implausible_voltage() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            volts=30.0,
        ),
        source_fresh=True,
    )

    assert result.volts.valid is False
    assert result.volts.message == "IMPLAUSIBLE DATA"


def test_engine_sensor_monitor_rejects_implausible_oil_temperature() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            oil_temp_f=500.0,
        ),
        source_fresh=True,
    )

    assert result.oil_temperature.valid is False
    assert (
        result.oil_temperature.message
        == "IMPLAUSIBLE DATA"
    )


def test_engine_sensor_monitor_rejects_implausible_fuel_pressure() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            fuel_pressure_psi=-1.0,
        ),
        source_fresh=True,
    )

    assert result.fuel_pressure.valid is False
    assert (
        result.fuel_pressure.message
        == "IMPLAUSIBLE DATA"
    )


def test_engine_sensor_monitor_rejects_implausible_fuel_flow() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            fuel_flow_gph=100.0,
        ),
        source_fresh=True,
    )

    assert result.fuel_flow.valid is False
    assert result.fuel_flow.message == "IMPLAUSIBLE DATA"
    
def test_engine_sensor_monitor_rejects_implausible_cht() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            cht_f=[
                325.0,
                325.0,
                700.0,
                325.0,
                325.0,
                325.0,
            ],
        ),
        source_fresh=True,
    )

    assert result.cht[2].valid is False
    assert result.cht[2].fresh is False
    assert (
        result.cht[2].message
        == "IMPLAUSIBLE DATA"
    )

    assert result.cht[0].valid is True


def test_engine_sensor_monitor_rejects_implausible_egt() -> None:
    monitor = EngineSensorMonitor()

    result = monitor.evaluate(
        EngineData(
            egt_f=[
                1325.0,
                2500.0,
            ],
        ),
        source_fresh=True,
    )

    assert result.egt[1].valid is False
    assert result.egt[1].fresh is False
    assert (
        result.egt[1].message
        == "IMPLAUSIBLE DATA"
    )

    assert result.egt[0].valid is True