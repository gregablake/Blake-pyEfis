from pyefis.user.blake_pfd.stratux_reader import (
    StratuxReader,
    decode_traffic_report,
    gdl90_crc,
)


# FAA GDL90 Public ICD,
# Section 3.5.2 example.
FAA_TRAFFIC_EXAMPLE = bytes.fromhex(
    "14 00 AB 45 49 1F EF 15 "
    "A8 89 78 0F 09 A9 07 B0 "
    "01 20 01 4E 38 32 35 56 "
    "20 20 20 00"
)


def _frame(
    message: bytes,
) -> bytes:

    crc = gdl90_crc(
        message
    )

    raw = (
        message
        + bytes(
            [
                crc & 0xFF,
                (crc >> 8) & 0xFF,
            ]
        )
    )

    escaped = bytearray()

    for byte in raw:

        if byte in {
            0x7D,
            0x7E,
        }:
            escaped.append(
                0x7D
            )

            escaped.append(
                byte ^ 0x20
            )

        else:
            escaped.append(
                byte
            )

    return (
        bytes([0x7E])
        + bytes(escaped)
        + bytes([0x7E])
    )


def test_gdl90_crc_matches_public_icd_heartbeat_example():

    message = bytes.fromhex(
        "00 81 41 DB D0 08 02"
    )

    assert (
        gdl90_crc(message)
        == 0x8BB3
    )


def test_decode_public_icd_traffic_example():

    target = (
        decode_traffic_report(
            FAA_TRAFFIC_EXAMPLE,
            now_s=123.0,
        )
    )

    assert target is not None

    assert (
        target.callsign
        == "N825V"
    )

    assert (
        target.address_type
        == 0
    )

    assert (
        target.participant_address
        == 0xAB4549
    )

    assert abs(
        target.latitude_deg
        - 44.90708
    ) < 0.00005

    assert abs(
        target.longitude_deg
        - (-122.99488)
    ) < 0.00005

    assert (
        target.pressure_alt_ft
        == 5000.0
    )

    assert (
        target.ground_speed_kt
        == 123.0
    )

    assert (
        target.vertical_speed_fpm
        == 64.0
    )

    assert abs(
        target.track_deg
        - 45.0
    ) < 0.01

    assert target.airborne
    assert target.track_valid
    assert target.ground_speed_valid
    assert target.position_valid

    assert target.nic == 10
    assert target.nacp == 9

    assert (
        target.emitter_category
        == 1
    )

    assert not target.traffic_alert

    assert (
        target.last_seen_s
        == 123.0
    )


def test_reader_accepts_valid_framed_traffic_report():

    reader = StratuxReader(
        bind_socket=False,
    )

    reader._consume_datagram(
        _frame(
            FAA_TRAFFIC_EXAMPLE
        ),
        now_s=100.0,
    )

    reader._prune_traffic(
        now_s=100.0,
    )

    assert (
        reader.valid_frame_count
        == 1
    )

    assert (
        reader.bad_crc_count
        == 0
    )

    assert (
        len(reader.traffic)
        == 1
    )

    assert (
        reader.traffic[0].callsign
        == "N825V"
    )


def test_reader_rejects_bad_crc():

    reader = StratuxReader(
        bind_socket=False,
    )

    packet = bytearray(
        _frame(
            FAA_TRAFFIC_EXAMPLE
        )
    )

    # Damage one CRC byte while
    # preserving framing.
    packet[-2] ^= 0x01

    reader._consume_datagram(
        bytes(packet),
        now_s=100.0,
    )

    reader._prune_traffic(
        now_s=100.0,
    )

    assert (
        reader.valid_frame_count
        == 0
    )

    assert (
        reader.bad_crc_count
        == 1
    )

    assert reader.traffic == []


def test_reader_expires_stale_target():

    reader = StratuxReader(
        bind_socket=False,
        target_timeout_s=5.0,
    )

    reader._consume_datagram(
        _frame(
            FAA_TRAFFIC_EXAMPLE
        ),
        now_s=100.0,
    )

    reader._prune_traffic(
        now_s=104.9,
    )

    assert (
        len(reader.traffic)
        == 1
    )

    reader._prune_traffic(
        now_s=105.1,
    )

    assert (
        reader.traffic
        == []
    )


def test_reader_decodes_escaped_gdl90_bytes():

    message = bytearray(
        FAA_TRAFFIC_EXAMPLE
    )

    # Force a GDL90 FLAG value into
    # the participant address so the
    # framing layer must escape it.
    message[2] = 0x7E

    reader = StratuxReader(
        bind_socket=False,
    )

    reader._consume_datagram(
        _frame(
            bytes(message)
        ),
        now_s=100.0,
    )

    reader._prune_traffic(
        now_s=100.0,
    )

    assert (
        len(reader.traffic)
        == 1
    )

    assert (
        reader.traffic[0]
        .participant_address
        == 0x7E4549
    )
