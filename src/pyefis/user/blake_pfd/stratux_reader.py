from __future__ import annotations

from dataclasses import dataclass
import socket
from time import monotonic


GDL90_FLAG = 0x7E
GDL90_ESCAPE = 0x7D
GDL90_ESCAPE_XOR = 0x20

GDL90_UPLINK_DATA = 0x07
GDL90_TRAFFIC_REPORT = 0x14

GDL90_UPLINK_MESSAGE_LENGTH = 436
GDL90_UPLINK_PAYLOAD_LENGTH = 432

# Keep only a small rolling window of raw uplinks.
# Downstream FIS-B decoding will consume these later.
MAX_RECENT_UPLINKS = 16

DEFAULT_PACKET_TIMEOUT_S = 3.0
DEFAULT_TARGET_TIMEOUT_S = 5.0
MAX_FRAME_BYTES = 2048


def _build_crc_table() -> tuple[int, ...]:
    table = []

    for value in range(256):
        crc = value << 8

        for _ in range(8):
            if crc & 0x8000:
                crc = (
                    (crc << 1)
                    ^ 0x1021
                ) & 0xFFFF
            else:
                crc = (
                    crc << 1
                ) & 0xFFFF

        table.append(crc)

    return tuple(table)


GDL90_CRC_TABLE = _build_crc_table()


@dataclass(frozen=True)
class UplinkData:
    """
    CRC-validated GDL90 0x07 Uplink Data.

    The payload remains raw UAT/FIS-B data here.
    Product decoding belongs in the weather layer.
    """

    time_of_reception: int
    payload: bytes
    last_seen_s: float


@dataclass
class TrafficTarget:
    # Original public fields retained first
    # so existing code remains compatible.
    callsign: str = "UNKNOWN"
    bearing_deg: float = 0.0
    distance_nm: float = 0.0
    relative_alt_ft: float = 0.0
    ground_speed_kt: float = 0.0
    track_deg: float = 0.0

    # Validated GDL90 target data.
    address_type: int = 0
    participant_address: int = 0

    latitude_deg: float | None = None
    longitude_deg: float | None = None
    pressure_alt_ft: float | None = None
    vertical_speed_fpm: float | None = None

    traffic_alert: bool = False
    airborne: bool = False

    track_valid: bool = False
    ground_speed_valid: bool = False
    position_valid: bool = False

    nic: int = 0
    nacp: int = 0
    emitter_category: int = 0

    last_seen_s: float = 0.0


@dataclass
class StratuxState:
    ok: bool = False
    traffic: list[TrafficTarget] | None = None

    # Recent CRC-valid GDL90 Uplink Data messages.
    uplinks: list[UplinkData] | None = None

    last_packet_time_s: float = 0.0

    # Separate weather/uplink freshness timestamp.
    # Do not infer weather freshness merely because
    # traffic or heartbeat packets are arriving.
    last_uplink_time_s: float = 0.0


def gdl90_crc(
    data: bytes,
) -> int:
    """
    GDL90 FCS algorithm from the public ICD.

    Polynomial: 0x1021
    Initial value: 0
    """

    crc = 0

    for byte in data:
        crc = (
            GDL90_CRC_TABLE[
                (crc >> 8) & 0xFF
            ]
            ^ ((crc << 8) & 0xFFFF)
            ^ byte
        ) & 0xFFFF

    return crc


def _signed_24(
    raw: int,
) -> int:
    if raw & 0x800000:
        return (
            raw
            - 0x1000000
        )

    return raw


def _signed_12(
    raw: int,
) -> int:
    if raw & 0x800:
        return (
            raw
            - 0x1000
        )

    return raw


def _decode_coordinate(
    b0: int,
    b1: int,
    b2: int,
) -> float:

    raw = (
        (b0 << 16)
        | (b1 << 8)
        | b2
    )

    signed = _signed_24(
        raw
    )

    return (
        signed
        * 180.0
        / float(1 << 23)
    )


def decode_uplink_data(
    message: bytes,
    *,
    now_s: float = 0.0,
) -> UplinkData | None:
    """
    Decode the GDL90 transport wrapper around
    a UAT uplink.

    This intentionally does NOT interpret FIS-B
    weather products yet.
    """

    if (
        len(message)
        != GDL90_UPLINK_MESSAGE_LENGTH
        or message[0]
        != GDL90_UPLINK_DATA
    ):
        return None

    # FAA GDL90 TOR is a 24-bit value with
    # least-significant byte transmitted first.
    time_of_reception = (
        message[1]
        | (message[2] << 8)
        | (message[3] << 16)
    )

    payload = bytes(
        message[4:]
    )

    if (
        len(payload)
        != GDL90_UPLINK_PAYLOAD_LENGTH
    ):
        return None

    return UplinkData(
        time_of_reception=(
            time_of_reception
        ),
        payload=payload,
        last_seen_s=float(
            now_s
        ),
    )


def decode_traffic_report(
    message: bytes,
    *,
    now_s: float = 0.0,
) -> TrafficTarget | None:
    """
    Decode one CRC-stripped GDL90
    Traffic Report.

    Traffic Report length is 28 bytes
    including Message ID 0x14.
    """

    if (
        len(message) != 28
        or message[0]
        != GDL90_TRAFFIC_REPORT
    ):
        return None

    status_address = message[1]

    alert_status = (
        status_address >> 4
    ) & 0x0F

    address_type = (
        status_address
        & 0x0F
    )

    participant_address = (
        (message[2] << 16)
        | (message[3] << 8)
        | message[4]
    )

    latitude_deg = (
        _decode_coordinate(
            message[5],
            message[6],
            message[7],
        )
    )

    longitude_deg = (
        _decode_coordinate(
            message[8],
            message[9],
            message[10],
        )
    )

    altitude_raw = (
        (message[11] << 4)
        | (message[12] >> 4)
    )

    if altitude_raw == 0xFFF:
        pressure_alt_ft = None
    else:
        pressure_alt_ft = float(
            altitude_raw * 25
            - 1000
        )

    miscellaneous = (
        message[12]
        & 0x0F
    )

    airborne = bool(
        miscellaneous
        & 0x08
    )

    track_type = (
        miscellaneous
        & 0x03
    )

    track_valid = (
        track_type != 0
    )

    nic = (
        message[13] >> 4
    ) & 0x0F

    nacp = (
        message[13]
        & 0x0F
    )

    horizontal_velocity_raw = (
        (message[14] << 4)
        | (message[15] >> 4)
    )

    ground_speed_valid = (
        horizontal_velocity_raw
        != 0xFFF
    )

    if ground_speed_valid:
        ground_speed_kt = float(
            horizontal_velocity_raw
        )
    else:
        ground_speed_kt = 0.0

    vertical_velocity_raw = (
        (
            (message[15] & 0x0F)
            << 8
        )
        | message[16]
    )

    if vertical_velocity_raw == 0x800:
        vertical_speed_fpm = None
    else:
        vertical_speed_fpm = float(
            _signed_12(
                vertical_velocity_raw
            )
            * 64
        )

    if track_valid:
        track_deg = (
            message[17]
            * 360.0
            / 256.0
        )
    else:
        track_deg = 0.0

    emitter_category = (
        message[18]
    )

    callsign = (
        message[19:27]
        .decode(
            "ascii",
            errors="replace",
        )
        .replace(
            "\x00",
            "",
        )
        .strip()
    )

    if not callsign:
        callsign = "UNKNOWN"

    # Per the GDL90 ICD, invalid
    # position is lat=0, lon=0, NIC=0.
    position_valid = not (
        nic == 0
        and abs(latitude_deg) < 1e-12
        and abs(longitude_deg) < 1e-12
    )

    return TrafficTarget(
        callsign=callsign,

        ground_speed_kt=(
            ground_speed_kt
        ),

        track_deg=track_deg,

        address_type=address_type,

        participant_address=(
            participant_address
        ),

        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,

        pressure_alt_ft=(
            pressure_alt_ft
        ),

        vertical_speed_fpm=(
            vertical_speed_fpm
        ),

        traffic_alert=(
            alert_status == 1
        ),

        airborne=airborne,

        track_valid=track_valid,

        ground_speed_valid=(
            ground_speed_valid
        ),

        position_valid=(
            position_valid
        ),

        nic=nic,
        nacp=nacp,

        emitter_category=(
            emitter_category
        ),

        last_seen_s=now_s,
    )


class StratuxReader:
    """
    Non-blocking Stratux GDL90 receiver.

    Frames must pass:
      * framing / escape decoding
      * CRC validation
      * message type / length validation

    Traffic is removed when stale.

    `StratuxState.ok` means valid GDL90
    data is currently arriving, not merely
    that the UDP socket opened.
    """

    def __init__(
        self,
        host: str = "192.168.10.1",
        port: int = 4000,
        *,
        packet_timeout_s: float = (
            DEFAULT_PACKET_TIMEOUT_S
        ),
        target_timeout_s: float = (
            DEFAULT_TARGET_TIMEOUT_S
        ),
        bind_socket: bool = True,
    ) -> None:

        self.host = host
        self.port = port

        self.packet_timeout_s = float(
            packet_timeout_s
        )

        self.target_timeout_s = float(
            target_timeout_s
        )

        self.ok = False
        self.last_packet_time_s = 0.0

        self.traffic: list[
            TrafficTarget
        ] = []

        self.uplinks: list[
            UplinkData
        ] = []

        self.last_uplink_time_s = 0.0

        self._traffic_by_key: dict[
            tuple[int, int],
            TrafficTarget,
        ] = {}

        self._frame = bytearray()
        self._in_frame = False
        self._escaped = False

        self.valid_frame_count = 0
        self.bad_crc_count = 0
        self.malformed_frame_count = 0

        self.sock = None

        if not bind_socket:
            return

        try:
            self.sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

            self.sock.setblocking(
                False
            )

            # IMPORTANT:
            #
            # 192.168.10.1 is the remote
            # Stratux, not this computer.
            #
            # Listen on all LOCAL interfaces
            # for Stratux GDL90 UDP traffic.
            self.sock.bind(
                (
                    "0.0.0.0",
                    self.port,
                )
            )

            self.ok = True

        except Exception as exc:
            print(
                "Stratux UDP listener "
                f"not active: {exc}"
            )

            self.sock = None
            self.ok = False

    def _process_frame(
        self,
        frame: bytes,
        *,
        now_s: float,
    ) -> None:

        if len(frame) < 3:
            self.malformed_frame_count += 1
            return

        message = frame[:-2]

        expected_crc = (
            frame[-2]
            | (frame[-1] << 8)
        )

        actual_crc = gdl90_crc(
            message
        )

        if (
            actual_crc
            != expected_crc
        ):
            self.bad_crc_count += 1
            return

        self.valid_frame_count += 1

        self.last_packet_time_s = (
            now_s
        )

        if not message:
            return

        message_id = message[0]

        if (
            message_id
            == GDL90_UPLINK_DATA
        ):
            uplink = (
                decode_uplink_data(
                    message,
                    now_s=now_s,
                )
            )

            if uplink is None:
                self.malformed_frame_count += 1
                return

            self.last_uplink_time_s = (
                now_s
            )

            self.uplinks.append(
                uplink
            )

            if (
                len(self.uplinks)
                > MAX_RECENT_UPLINKS
            ):
                self.uplinks = (
                    self.uplinks[
                        -MAX_RECENT_UPLINKS:
                    ]
                )

            return

        if (
            message_id
            != GDL90_TRAFFIC_REPORT
        ):
            return

        target = (
            decode_traffic_report(
                message,
                now_s=now_s,
            )
        )

        if target is None:
            self.malformed_frame_count += 1
            return

        # Do not place a target on the
        # moving map unless its position
        # is explicitly valid.
        if not target.position_valid:
            return

        key = (
            target.address_type,
            target.participant_address,
        )

        self._traffic_by_key[
            key
        ] = target

    def _consume_datagram(
        self,
        data: bytes,
        *,
        now_s: float,
    ) -> None:

        for byte in data:

            if byte == GDL90_FLAG:

                if (
                    self._in_frame
                    and self._frame
                ):
                    self._process_frame(
                        bytes(
                            self._frame
                        ),
                        now_s=now_s,
                    )

                self._frame.clear()

                self._escaped = False
                self._in_frame = True
                continue

            if not self._in_frame:
                continue

            if self._escaped:

                self._frame.append(
                    byte
                    ^ GDL90_ESCAPE_XOR
                )

                self._escaped = False
                continue

            if byte == GDL90_ESCAPE:
                self._escaped = True
                continue

            self._frame.append(
                byte
            )

            if (
                len(self._frame)
                > MAX_FRAME_BYTES
            ):
                self._frame.clear()

                self._escaped = False
                self._in_frame = False

                self.malformed_frame_count += 1

    def _prune_traffic(
        self,
        *,
        now_s: float,
    ) -> None:

        stale_keys = [
            key
            for key, target
            in self._traffic_by_key.items()
            if (
                now_s
                - target.last_seen_s
                > self.target_timeout_s
            )
        ]

        for key in stale_keys:
            del self._traffic_by_key[
                key
            ]

        # Alerts first, then stable ordering.
        self.traffic = sorted(
            self._traffic_by_key.values(),
            key=lambda target: (
                not target.traffic_alert,
                target.callsign,
                target.participant_address,
            ),
        )

    def read(
        self,
    ) -> StratuxState:

        if (
            not self.ok
            or self.sock is None
        ):
            return StratuxState(
                ok=False,
                traffic=[],
                uplinks=list(
                    self.uplinks
                ),
                last_packet_time_s=(
                    self.last_packet_time_s
                ),
                last_uplink_time_s=(
                    self.last_uplink_time_s
                ),
            )

        now_s = monotonic()

        try:
            while True:

                data, _addr = (
                    self.sock.recvfrom(
                        8192
                    )
                )

                self._consume_datagram(
                    data,
                    now_s=now_s,
                )

        except BlockingIOError:
            pass

        except Exception as exc:

            print(
                "Stratux read failed: "
                f"{exc}"
            )

            self.ok = False

            return StratuxState(
                ok=False,
                traffic=[],
                uplinks=list(
                    self.uplinks
                ),
                last_packet_time_s=(
                    self.last_packet_time_s
                ),
                last_uplink_time_s=(
                    self.last_uplink_time_s
                ),
            )

        self._prune_traffic(
            now_s=now_s,
        )

        packet_fresh = (
            self.last_packet_time_s > 0.0
            and (
                now_s
                - self.last_packet_time_s
                <= self.packet_timeout_s
            )
        )

        return StratuxState(
            ok=bool(
                self.ok
                and packet_fresh
            ),

            traffic=list(
                self.traffic
            ),

            uplinks=list(
                self.uplinks
            ),

            last_packet_time_s=(
                self.last_packet_time_s
            ),

            last_uplink_time_s=(
                self.last_uplink_time_s
            ),
        )


def demo() -> None:
    reader = StratuxReader()

    state = reader.read()

    print(
        "===== Stratux Reader Demo ====="
    )

    print(state)


if __name__ == "__main__":
    demo()
