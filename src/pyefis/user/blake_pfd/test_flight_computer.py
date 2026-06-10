from pyefis.user.blake_pfd.flight_computer import FlightComputer
from pyefis.user.blake_pfd.sensors_sim import SimulatedSensorSource


def main() -> None:
    sensor = SimulatedSensorSource()
    fc = FlightComputer()
    raw = sensor.read()
    flight = fc.update(raw)
    print(flight)


if __name__ == "__main__":
    main()
