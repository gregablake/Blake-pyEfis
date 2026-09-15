from pyefis.user.blake_pfd.stratux_reader import (
    GDL90_UPLINK_DATA,
    GDL90_UPLINK_MESSAGE_LENGTH,
    GDL90_UPLINK_PAYLOAD_LENGTH,
    StratuxReader,
    decode_uplink_data,
    gdl90_crc,
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


def _uplink_message() -> bytes:
    payload = bytes(
        index % 256
        for index in range(
            GDL90_UPLINK_PAYLOAD_LENGTH
        )
    )

    # TOR = 0x030201, transmitted LSB first.
    message = (
        bytes(
            [
                GDL90_UPLINK_DATA,
                0x01,
                0x02,
                0x03,
            ]
        )
        + payload
    )

    assert (
        len(message)
        == GDL90_UPLINK_MESSAGE_LENGTH
    )

    return message


def test_decode_gdl90_uplink_wrapper():

    message = _uplink_message()

    result = decode_uplink_data(
        message,
        now_s=123.5,
    )

    assert result is not None

    assert (
        result.time_of_reception
        == 0x030201
    )

    assert (
        len(result.payload)
        == 432
    )

    assert (
        result.payload
        == message[4:]
    )

    assert (
        result.last_seen_s
        == 123.5
    )


def test_uplink_wrong_length_fails_closed():

    result = decode_uplink_data(
        bytes(
            [
                GDL90_UPLINK_DATA,
                0x00,
                0x00,
                0x00,
            ]
        ),
        now_s=1.0,
    )

    assert result is None


def test_reader_accepts_crc_valid_weather_uplink():

    reader = StratuxReader(
        bind_socket=False,
    )

    reader._consume_datagram(
        _frame(
            _uplink_message()
        ),
        now_s=250.0,
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
        len(reader.uplinks)
        == 1
    )

    assert (
        reader.last_uplink_time_s
        == 250.0
    )

    assert (
        reader.uplinks[0]
        .time_of_reception
        == 0x030201
    )


def test_reader_rejects_bad_uplink_crc():

    reader = StratuxReader(
        bind_socket=False,
    )

    packet = bytearray(
        _frame(
            _uplink_message()
        )
    )

    packet[-2] ^= 0x01

    reader._consume_datagram(
        bytes(packet),
        now_s=250.0,
    )

    assert reader.uplinks == []

    assert (
        reader.bad_crc_count
        == 1
    )

    assert (
        reader.last_uplink_time_s
        == 0.0
    )
