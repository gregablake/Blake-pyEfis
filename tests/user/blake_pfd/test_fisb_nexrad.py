from pyefis.user.blake_pfd.core.fisb_nexrad import (
    PRODUCT_CONUS_NEXRAD,
    PRODUCT_REGIONAL_NEXRAD,
    block_location,
    decode_nexrad_uplink,
)


def _info_frame(
    *,
    product_id: int,
    fisb_data: bytes,
    segmented: bool = False,
    frame_type: int = 0,
) -> bytes:

    # Time option 0:
    # APDU product header + HH/MM = 4 bytes
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

    if segmented:
        raw_1 |= 0x02

    raw = bytes(
        [
            raw_0,
            raw_1,
            0x00,
            0x00,
        ]
    ) + fisb_data

    length = len(raw)

    return bytes(
        [
            length >> 1,
            (
                ((length & 1) << 7)
                | (
                    frame_type
                    & 0x0F
                )
            ),
        ]
    ) + raw


def _uplink(
    *frames: bytes,
    app_data_valid: bool = True,
) -> bytes:

    payload = bytearray(
        432
    )

    if app_data_valid:
        payload[6] |= 0x20

    position = 8

    for frame in frames:
        end = (
            position
            + len(frame)
        )

        assert end <= 432

        payload[
            position:end
        ] = frame

        position = end

    # Remaining zero bytes naturally create
    # the terminating zero-length frame.
    return bytes(
        payload
    )


def test_block_location_known_ring():

    (
        lat_north,
        lon_west,
        height,
        width,
    ) = block_location(
        block_number=450,
        south_hemisphere=False,
        scale_factor=0,
    )

    assert abs(
        lat_north
        - (8.0 / 60.0)
    ) < 1e-9

    assert lon_west == 0.0

    assert abs(
        height
        - (4.0 / 60.0)
    ) < 1e-9

    assert abs(
        width
        - (48.0 / 60.0)
    ) < 1e-9


def test_decode_regional_rle_block():

    # Block number 450.
    #
    # Four 32-bin RLE runs:
    # levels 1, 2, 3, 4.
    fisb_data = bytes(
        [
            0x80,
            0x01,
            0xC2,
            0xF9,
            0xFA,
            0xFB,
            0xFC,
        ]
    )

    blocks = decode_nexrad_uplink(
        _uplink(
            _info_frame(
                product_id=(
                    PRODUCT_REGIONAL_NEXRAD
                ),
                fisb_data=fisb_data,
            )
        )
    )

    assert len(blocks) == 1

    block = blocks[0]

    assert (
        block.product_id
        == PRODUCT_REGIONAL_NEXRAD
    )

    assert len(
        block.intensity
    ) == 128

    assert (
        block.intensity[:32]
        == (1,) * 32
    )

    assert (
        block.intensity[32:64]
        == (2,) * 32
    )

    assert (
        block.intensity[64:96]
        == (3,) * 32
    )

    assert (
        block.intensity[96:]
        == (4,) * 32
    )


def test_decode_conus_empty_block_bitmap():

    # Product 64, block 450.
    #
    # Bitmap length 1. The mandatory bit-3
    # produces block 450.
    fisb_data = bytes(
        [
            0x00,
            0x01,
            0xC2,
            0x01,
        ]
    )

    blocks = decode_nexrad_uplink(
        _uplink(
            _info_frame(
                product_id=(
                    PRODUCT_CONUS_NEXRAD
                ),
                fisb_data=fisb_data,
            )
        )
    )

    assert len(blocks) == 1

    assert (
        blocks[0].product_id
        == PRODUCT_CONUS_NEXRAD
    )

    assert (
        blocks[0].intensity
        == (1,) * 128
    )


def test_invalid_application_data_fails_closed():

    blocks = decode_nexrad_uplink(
        _uplink(
            app_data_valid=False,
        )
    )

    assert blocks == []


def test_segmented_nexrad_fails_closed():

    fisb_data = bytes(
        [
            0x80,
            0x01,
            0xC2,
            0xF9,
            0xFA,
            0xFB,
            0xFC,
        ]
    )

    blocks = decode_nexrad_uplink(
        _uplink(
            _info_frame(
                product_id=(
                    PRODUCT_REGIONAL_NEXRAD
                ),
                fisb_data=fisb_data,
                segmented=True,
            )
        )
    )

    assert blocks == []


def test_non_nexrad_product_is_ignored():

    blocks = decode_nexrad_uplink(
        _uplink(
            _info_frame(
                product_id=413,
                fisb_data=(
                    b"NOT NEXRAD"
                ),
            )
        )
    )

    assert blocks == []
