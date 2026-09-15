from __future__ import annotations

from dataclasses import dataclass


# Ported from the Stratux UAT/FIS-B
# Global Block Representation decoder.
BLOCK_WIDTH_DEG = 48.0 / 60.0
WIDE_BLOCK_WIDTH_DEG = 96.0 / 60.0
BLOCK_HEIGHT_DEG = 4.0 / 60.0

BLOCK_THRESHOLD = 405000
BLOCKS_PER_RING = 450

PRODUCT_REGIONAL_NEXRAD = 63
PRODUCT_CONUS_NEXRAD = 64

UAT_UPLINK_PAYLOAD_BYTES = 432
UAT_APPLICATION_OFFSET = 8

MAX_INFO_FRAMES = 424 // 6

FISB_FRAME_TYPE = 0


@dataclass(frozen=True)
class NexradBlock:
    product_id: int
    scale_factor: int

    lat_north_deg: float
    lon_west_deg: float

    height_deg: float
    width_deg: float

    # NEXRAD values are 3-bit levels, 0..7.
    intensity: tuple[int, ...]


def block_location(
    *,
    block_number: int,
    south_hemisphere: bool,
    scale_factor: int,
) -> tuple[
    float,
    float,
    float,
    float,
]:
    """
    Resolve one FIS-B global block number into
    geographic block bounds.

    Return:
        lat_north,
        lon_west,
        height,
        width
    """

    if scale_factor == 1:
        real_scale = 5.0

    elif scale_factor == 2:
        real_scale = 9.0

    else:
        # Matches Stratux handling for scale 0/3.
        real_scale = 1.0

    block_number = int(
        block_number
    )

    if (
        block_number
        >= BLOCK_THRESHOLD
    ):
        # High-latitude blocks are paired.
        block_number &= ~1

    raw_lat = (
        BLOCK_HEIGHT_DEG
        * int(
            block_number
            / BLOCKS_PER_RING
        )
    )

    raw_lon = (
        (
            block_number
            % BLOCKS_PER_RING
        )
        * BLOCK_WIDTH_DEG
    )

    if (
        block_number
        >= BLOCK_THRESHOLD
    ):
        lon_size = (
            WIDE_BLOCK_WIDTH_DEG
            * real_scale
        )
    else:
        lon_size = (
            BLOCK_WIDTH_DEG
            * real_scale
        )

    lat_size = (
        BLOCK_HEIGHT_DEG
        * real_scale
    )

    if south_hemisphere:
        raw_lat = -raw_lat
    else:
        raw_lat += (
            BLOCK_HEIGHT_DEG
        )

    if raw_lon > 180.0:
        raw_lon -= 360.0

    return (
        raw_lat,
        raw_lon,
        lat_size,
        lon_size,
    )


def _extract_fisb_data(
    raw_data: bytes,
) -> bytes | None:
    """
    Strip the FIS-B APDU product/time header.

    NEXRAD 63/64 is not expected to use APDU
    segmentation. Segmented data therefore fails
    closed until explicit reassembly exists.
    """

    if len(raw_data) < 3:
        return None

    segmented = bool(
        raw_data[1] & 0x02
    )

    if segmented:
        return None

    time_option = (
        (
            raw_data[1]
            & 0x01
        )
        << 1
    ) | (
        raw_data[2]
        >> 7
    )

    if time_option == 0:
        offset = 4

    elif time_option == 1:
        offset = 5

    elif time_option == 2:
        offset = 5

    elif time_option == 3:
        offset = 6

    else:
        return None

    if len(raw_data) < offset:
        return None

    return bytes(
        raw_data[offset:]
    )


def _decode_nexrad_data(
    *,
    product_id: int,
    fisb_data: bytes,
) -> list[NexradBlock]:
    if len(fisb_data) < 4:
        return []

    first = fisb_data[0]

    rle_flag = bool(
        first & 0x80
    )

    south_hemisphere = bool(
        first & 0x40
    )

    scale_factor = (
        first & 0x30
    ) >> 4

    block_number = (
        (
            first
            & 0x0F
        )
        << 16
    ) | (
        fisb_data[1]
        << 8
    ) | fisb_data[2]

    if rle_flag:
        (
            lat_north,
            lon_west,
            height,
            width,
        ) = block_location(
            block_number=(
                block_number
            ),
            south_hemisphere=(
                south_hemisphere
            ),
            scale_factor=(
                scale_factor
            ),
        )

        intensity: list[int] = []

        for encoded in fisb_data[3:]:
            level = (
                encoded
                & 0x07
            )

            run_length = (
                encoded >> 3
            ) + 1

            intensity.extend(
                [level]
                * run_length
            )

            # A GBR weather block contains
            # 128 bins. Anything beyond this
            # cannot belong to this block.
            if len(intensity) > 128:
                return []

        # Require a complete block rather than
        # rendering a partially decoded product.
        if len(intensity) != 128:
            return []

        return [
            NexradBlock(
                product_id=(
                    product_id
                ),
                scale_factor=(
                    scale_factor
                ),
                lat_north_deg=(
                    lat_north
                ),
                lon_west_deg=(
                    lon_west
                ),
                height_deg=height,
                width_deg=width,
                intensity=tuple(
                    intensity
                ),
            )
        ]

    # Empty-block bitmap representation.
    if (
        block_number
        >= BLOCK_THRESHOLD
    ):
        row_start = (
            block_number
            - (
                (
                    block_number
                    - BLOCK_THRESHOLD
                )
                % 225
            )
        )

        row_size = 225

    else:
        row_start = (
            block_number
            - (
                block_number
                % 450
            )
        )

        row_size = 450

    row_offset = (
        block_number
        - row_start
    )

    bitmap_length = (
        fisb_data[3]
        & 0x0F
    )

    # Byte 3 participates both in the bitmap
    # length and the first bitmap byte.
    if len(fisb_data) < (
        bitmap_length + 3
    ):
        return []

    blocks: list[
        NexradBlock
    ] = []

    for index in range(
        bitmap_length
    ):
        if index == 0:
            bitmap_byte = (
                (
                    fisb_data[3]
                    & 0xF0
                )
                | 0x08
            )
        else:
            bitmap_byte = (
                fisb_data[
                    index + 3
                ]
            )

        for bit in range(8):
            if not (
                bitmap_byte
                & (1 << bit)
            ):
                continue

            row_x = (
                row_offset
                + 8 * index
                + bit
                - 3
            ) % row_size

            resolved_block = (
                row_start
                + row_x
            )

            (
                lat_north,
                lon_west,
                height,
                width,
            ) = block_location(
                block_number=(
                    resolved_block
                ),
                south_hemisphere=(
                    south_hemisphere
                ),
                scale_factor=(
                    scale_factor
                ),
            )

            # For CONUS product 64, an empty
            # block is represented by level 1
            # in Stratux's reference decoder.
            empty_level = (
                1
                if product_id
                == PRODUCT_CONUS_NEXRAD
                else 0
            )

            blocks.append(
                NexradBlock(
                    product_id=(
                        product_id
                    ),
                    scale_factor=(
                        scale_factor
                    ),
                    lat_north_deg=(
                        lat_north
                    ),
                    lon_west_deg=(
                        lon_west
                    ),
                    height_deg=height,
                    width_deg=width,
                    intensity=tuple(
                        [empty_level]
                        * 128
                    ),
                )
            )

    return blocks


def decode_nexrad_uplink(
    payload: bytes,
) -> list[NexradBlock]:
    """
    Decode Product 63/64 NEXRAD frames from one
    432-byte UAT uplink payload.

    Invalid/truncated/segmented data is ignored.
    """

    if (
        len(payload)
        != UAT_UPLINK_PAYLOAD_BYTES
    ):
        return []

    # UAT uplink byte 6 bit 5:
    # application data valid.
    if not (
        payload[6]
        & 0x20
    ):
        return []

    app_data = payload[
        UAT_APPLICATION_OFFSET:
    ]

    position = 0
    frame_count = 0

    blocks: list[
        NexradBlock
    ] = []

    while (
        frame_count
        < MAX_INFO_FRAMES
        and position + 2
        <= len(app_data)
    ):
        header_0 = (
            app_data[position]
        )

        header_1 = (
            app_data[
                position + 1
            ]
        )

        frame_length = (
            (header_0 << 1)
            | (header_1 >> 7)
        )

        frame_type = (
            header_1
            & 0x0F
        )

        if frame_length == 0:
            break

        frame_start = (
            position + 2
        )

        frame_end = (
            frame_start
            + frame_length
        )

        if (
            frame_end
            > len(app_data)
        ):
            # Truncated frame. Fail closed for
            # the remainder of this uplink.
            break

        raw_data = bytes(
            app_data[
                frame_start:
                frame_end
            ]
        )

        position = frame_end
        frame_count += 1

        if (
            frame_type
            != FISB_FRAME_TYPE
        ):
            continue

        if len(raw_data) < 2:
            continue

        product_id = (
            (
                raw_data[0]
                & 0x1F
            )
            << 6
        ) | (
            raw_data[1]
            >> 2
        )

        if product_id not in {
            PRODUCT_REGIONAL_NEXRAD,
            PRODUCT_CONUS_NEXRAD,
        }:
            continue

        fisb_data = (
            _extract_fisb_data(
                raw_data
            )
        )

        if fisb_data is None:
            continue

        blocks.extend(
            _decode_nexrad_data(
                product_id=(
                    product_id
                ),
                fisb_data=(
                    fisb_data
                ),
            )
        )

    return blocks
