from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import isfinite
from time import monotonic

from pyefis.user.blake_pfd.core.fisb_nexrad import (
    NexradBlock,
    decode_nexrad_uplink,
)


DEFAULT_NEXRAD_MAX_AGE_S = 15.0 * 60.0


@dataclass
class WeatherMetar:
    airport_id: str
    age_min: float = 0.0
    flight_category: str = "UNK"
    wind_text: str = ""
    altimeter_inhg: float = 29.92
    raw_text: str = ""


@dataclass
class WeatherState:
    ok: bool = False

    metars: list[
        WeatherMetar
    ] | None = None

    nexrad_blocks: list[
        NexradBlock
    ] | None = None

    last_update_s: float = 0.0


@dataclass
class _CachedNexrad:
    block: NexradBlock
    received_s: float


class WeatherReader:
    """
    FIS-B weather state/cache.

    Raw GDL90/UAT transport remains in
    StratuxReader.

    This layer:
      * decodes FIS-B NEXRAD products
      * deduplicates geographic blocks
      * tracks age
      * expires stale weather
      * fails closed when no fresh radar exists
    """

    def __init__(
        self,
        *,
        nexrad_max_age_s: float = (
            DEFAULT_NEXRAD_MAX_AGE_S
        ),
    ) -> None:

        self.nexrad_max_age_s = float(
            nexrad_max_age_s
        )

        if (
            not isfinite(
                self.nexrad_max_age_s
            )
            or self.nexrad_max_age_s <= 0.0
        ):
            raise ValueError(
                "nexrad_max_age_s must be "
                "positive and finite"
            )

        self.metars: list[
            WeatherMetar
        ] = []

        self._nexrad: dict[
            tuple[
                int,
                int,
                float,
                float,
                float,
                float,
            ],
            _CachedNexrad,
        ] = {}

        self.last_update_s = 0.0

        # StratuxReader exposes a small rolling window
        # of recent uplinks. The PFD may therefore see
        # the same UplinkData objects on many paint
        # cycles. Track a bounded set so each uplink is
        # decoded only once.
        self._processed_uplink_keys: set[
            tuple[
                float,
                int,
                bytes,
            ]
        ] = set()

        self._processed_uplink_order = deque()

        self._processed_uplink_limit = 128

    @staticmethod
    def _block_key(
        block: NexradBlock,
    ) -> tuple[
        int,
        int,
        float,
        float,
        float,
        float,
    ]:
        """
        Stable geographic/product identity.

        Rounded coordinates prevent insignificant
        floating-point representation differences
        from creating duplicate radar blocks.
        """

        return (
            int(
                block.product_id
            ),
            int(
                block.scale_factor
            ),
            round(
                block.lat_north_deg,
                8,
            ),
            round(
                block.lon_west_deg,
                8,
            ),
            round(
                block.height_deg,
                8,
            ),
            round(
                block.width_deg,
                8,
            ),
        )

    def ingest_uplinks(
        self,
        uplinks,
        *,
        now_s: float | None = None,
    ) -> int:
        """
        Decode newly received Stratux uplinks.

        Returns the number of NEXRAD blocks decoded
        from this ingestion call.

        An uplink that contains no supported NEXRAD
        product does NOT make weather valid.
        """

        if now_s is None:
            now_s = monotonic()

        now_s = float(
            now_s
        )

        if not isfinite(
            now_s
        ):
            raise ValueError(
                "now_s must be finite"
            )

        decoded_count = 0

        for uplink in (
            uplinks
            or []
        ):
            payload = getattr(
                uplink,
                "payload",
                None,
            )

            if not isinstance(
                payload,
                (bytes, bytearray),
            ):
                continue

            payload_bytes = bytes(
                payload
            )

            received_s = getattr(
                uplink,
                "last_seen_s",
                now_s,
            )

            try:
                received_s = float(
                    received_s
                )
            except (
                TypeError,
                ValueError,
            ):
                received_s = now_s

            if not isfinite(
                received_s
            ):
                received_s = now_s

            time_of_reception = getattr(
                uplink,
                "time_of_reception",
                0,
            )

            try:
                time_of_reception = int(
                    time_of_reception
                )
            except (
                TypeError,
                ValueError,
            ):
                time_of_reception = 0

            uplink_key = (
                received_s,
                time_of_reception,
                payload_bytes,
            )

            if (
                uplink_key
                in self._processed_uplink_keys
            ):
                continue

            self._processed_uplink_keys.add(
                uplink_key
            )

            self._processed_uplink_order.append(
                uplink_key
            )

            while (
                len(
                    self._processed_uplink_order
                )
                > self._processed_uplink_limit
            ):
                old_key = (
                    self._processed_uplink_order
                    .popleft()
                )

                self._processed_uplink_keys.discard(
                    old_key
                )

            blocks = decode_nexrad_uplink(
                payload_bytes
            )

            for block in blocks:
                key = self._block_key(
                    block
                )

                existing = (
                    self._nexrad.get(
                        key
                    )
                )

                # Do not allow an older replayed
                # uplink to overwrite newer radar.
                if (
                    existing is not None
                    and existing.received_s
                    > received_s
                ):
                    continue

                self._nexrad[
                    key
                ] = _CachedNexrad(
                    block=block,
                    received_s=(
                        received_s
                    ),
                )

                self.last_update_s = max(
                    self.last_update_s,
                    received_s,
                )

                decoded_count += 1

        self._prune(
            now_s=now_s
        )

        return decoded_count

    def _prune(
        self,
        *,
        now_s: float,
    ) -> None:

        stale = [
            key
            for key, cached
            in self._nexrad.items()
            if (
                now_s
                - cached.received_s
                > self.nexrad_max_age_s
            )
        ]

        for key in stale:
            del self._nexrad[
                key
            ]

    def read(
        self,
        *,
        now_s: float | None = None,
    ) -> WeatherState:

        if now_s is None:
            now_s = monotonic()

        now_s = float(
            now_s
        )

        if not isfinite(
            now_s
        ):
            raise ValueError(
                "now_s must be finite"
            )

        self._prune(
            now_s=now_s
        )

        cached_blocks = sorted(
            self._nexrad.values(),
            key=lambda cached: (
                cached.block.product_id,
                cached.block.lat_north_deg,
                cached.block.lon_west_deg,
                cached.block.scale_factor,
            ),
        )

        blocks = [
            cached.block
            for cached
            in cached_blocks
        ]

        return WeatherState(
            ok=bool(
                blocks
            ),
            metars=list(
                self.metars
            ),
            nexrad_blocks=blocks,
            last_update_s=(
                self.last_update_s
            ),
        )


def demo() -> None:
    reader = WeatherReader()

    print(
        "===== Weather Reader Demo ====="
    )

    print(
        reader.read()
    )


if __name__ == "__main__":
    demo()
