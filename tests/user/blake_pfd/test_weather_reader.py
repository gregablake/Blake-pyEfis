from pyefis.user.blake_pfd.stratux_reader import (
    UplinkData,
)
from pyefis.user.blake_pfd.weather_reader import (
    WeatherReader,
)


PRODUCT_REGIONAL_NEXRAD = 63


def _info_frame(
    *,
    product_id: int,
    fisb_data: bytes,
) -> bytes:

    raw_0 = (
        product_id >> 6
    ) & 0x1F

    raw_1 = (
        (
            product_id
            & 0x3F
        )
        << 2
    )

    # Time option 0.
    raw = bytes(
        [
            raw_0,
            raw_1,
            0x00,
            0x00,
        ]
    ) + fisb_data

    length = len(
        raw
    )

    return bytes(
        [
            length >> 1,
            (
                (length & 1)
                << 7
            ),
        ]
    ) + raw


def _payload(
    *,
    first_level: int = 1,
) -> bytes:

    payload = bytearray(
        432
    )

    # Application data valid.
    payload[6] |= 0x20

    # Block 450, RLE encoded.
    #
    # Four 32-bin runs.
    levels = [
        first_level,
        2,
        3,
        4,
    ]

    fisb_data = bytes(
        [
            0x80,
            0x01,
            0xC2,
        ]
        + [
            (
                (31 << 3)
                | level
            )
            for level in levels
        ]
    )

    frame = _info_frame(
        product_id=(
            PRODUCT_REGIONAL_NEXRAD
        ),
        fisb_data=fisb_data,
    )

    payload[
        8:
        8 + len(frame)
    ] = frame

    return bytes(
        payload
    )


def _uplink(
    *,
    seen_s: float,
    first_level: int = 1,
) -> UplinkData:

    return UplinkData(
        time_of_reception=1,
        payload=_payload(
            first_level=(
                first_level
            )
        ),
        last_seen_s=seen_s,
    )


def test_weather_starts_unavailable():

    reader = WeatherReader(
        nexrad_max_age_s=900.0,
    )

    state = reader.read(
        now_s=100.0
    )

    assert not state.ok

    assert (
        state.nexrad_blocks
        == []
    )


def test_ingest_valid_nexrad_makes_weather_available():

    reader = WeatherReader(
        nexrad_max_age_s=900.0,
    )

    count = reader.ingest_uplinks(
        [
            _uplink(
                seen_s=100.0,
            )
        ],
        now_s=100.0,
    )

    assert count == 1

    state = reader.read(
        now_s=100.0
    )

    assert state.ok

    assert len(
        state.nexrad_blocks
    ) == 1

    assert (
        state.last_update_s
        == 100.0
    )


def test_nexrad_expires_when_stale():

    reader = WeatherReader(
        nexrad_max_age_s=10.0,
    )

    reader.ingest_uplinks(
        [
            _uplink(
                seen_s=100.0,
            )
        ],
        now_s=100.0,
    )

    fresh = reader.read(
        now_s=109.9
    )

    assert fresh.ok

    stale = reader.read(
        now_s=110.1
    )

    assert not stale.ok

    assert (
        stale.nexrad_blocks
        == []
    )


def test_newer_same_block_replaces_old_block():

    reader = WeatherReader(
        nexrad_max_age_s=900.0,
    )

    reader.ingest_uplinks(
        [
            _uplink(
                seen_s=100.0,
                first_level=1,
            )
        ],
        now_s=100.0,
    )

    reader.ingest_uplinks(
        [
            _uplink(
                seen_s=110.0,
                first_level=5,
            )
        ],
        now_s=110.0,
    )

    state = reader.read(
        now_s=110.0
    )

    assert len(
        state.nexrad_blocks
    ) == 1

    block = (
        state.nexrad_blocks[0]
    )

    assert (
        block.intensity[:32]
        == (5,) * 32
    )

    assert (
        state.last_update_s
        == 110.0
    )


def test_older_replayed_block_cannot_replace_newer():

    reader = WeatherReader(
        nexrad_max_age_s=900.0,
    )

    reader.ingest_uplinks(
        [
            _uplink(
                seen_s=110.0,
                first_level=5,
            )
        ],
        now_s=110.0,
    )

    reader.ingest_uplinks(
        [
            _uplink(
                seen_s=100.0,
                first_level=1,
            )
        ],
        now_s=111.0,
    )

    state = reader.read(
        now_s=111.0
    )

    assert len(
        state.nexrad_blocks
    ) == 1

    assert (
        state.nexrad_blocks[0]
        .intensity[:32]
        == (5,) * 32
    )


def test_non_nexrad_uplink_does_not_mark_weather_ok():

    reader = WeatherReader(
        nexrad_max_age_s=900.0,
    )

    empty_payload = bytes(
        432
    )

    count = reader.ingest_uplinks(
        [
            UplinkData(
                time_of_reception=0,
                payload=empty_payload,
                last_seen_s=100.0,
            )
        ],
        now_s=100.0,
    )

    assert count == 0

    assert not reader.read(
        now_s=100.0
    ).ok


def test_same_uplink_is_decoded_only_once():

    reader = WeatherReader(
        nexrad_max_age_s=900.0,
    )

    uplink = _uplink(
        seen_s=100.0,
        first_level=3,
    )

    first = reader.ingest_uplinks(
        [uplink],
        now_s=100.0,
    )

    second = reader.ingest_uplinks(
        [uplink],
        now_s=101.0,
    )

    assert first == 1
    assert second == 0

    state = reader.read(
        now_s=101.0
    )

    assert state.ok

    assert len(
        state.nexrad_blocks
    ) == 1
