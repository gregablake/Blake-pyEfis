from __future__ import annotations

from dataclasses import dataclass
import socket
from time import monotonic


@dataclass
class TrafficTarget:
    callsign: str = "UNKNOWN"
    bearing_deg: float = 0.0
    distance_nm: float = 0.0
    relative_alt_ft: float = 0.0
    ground_speed_kt: float = 0.0
    track_deg: float = 0.0


@dataclass
class StratuxState:
    ok: bool = False
    traffic: list[TrafficTarget] | None = None
    last_packet_time_s: float = 0.0


class StratuxReader:
    """
    Stratux UDP listener foundation.

    Later this will parse GDL90 traffic/weather.
    This first version safely listens and stores packet timing.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 4000) -> None:
        self.host = host
        self.port = port
        self.ok = False
        self.last_packet_time_s = 0.0
        self.traffic: list[TrafficTarget] = []

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setblocking(False)
            self.sock.bind((self.host, self.port))
            self.ok = True
        except Exception as exc:
            print(f"Stratux UDP listener not active: {exc}")
            self.sock = None
            self.ok = False

    def read(self) -> StratuxState:
        if not self.ok or self.sock is None:
            return StratuxState(ok=False, traffic=[])

        try:
            while True:
                data, _addr = self.sock.recvfrom(4096)
                self.last_packet_time_s = monotonic()

                # Placeholder: real GDL90 parsing comes next.
                _ = data

        except BlockingIOError:
            pass
        except Exception as exc:
            print(f"Stratux read failed: {exc}")
            self.ok = False

        return StratuxState(
            ok=self.ok,
            traffic=self.traffic,
            last_packet_time_s=self.last_packet_time_s,
        )


def demo() -> None:
    reader = StratuxReader()
    state = reader.read()

    print("===== Stratux Reader Demo =====")
    print(state)


if __name__ == "__main__":
    demo()