from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class HistorySample:
    timestamp_s: float
    value: float


class RollingHistory:
    def __init__(
        self,
        window_s: float = 60.0,
    ) -> None:
        if window_s <= 0:
            raise ValueError("window_s must be greater than zero")

        self.window_s = float(window_s)
        self._samples: deque[HistorySample] = deque()

    def add(
        self,
        value: float,
        timestamp_s: float | None = None,
    ) -> None:
        if timestamp_s is None:
            timestamp_s = monotonic()

        sample = HistorySample(
            timestamp_s=float(timestamp_s),
            value=float(value),
        )

        self._samples.append(sample)
        self._trim(sample.timestamp_s)

    def clear(self) -> None:
        self._samples.clear()

    @property
    def samples(self) -> tuple[HistorySample, ...]:
        return tuple(self._samples)

    @property
    def sample_count(self) -> int:
        return len(self._samples)

    @property
    def oldest(self) -> HistorySample | None:
        if not self._samples:
            return None

        return self._samples[0]

    @property
    def newest(self) -> HistorySample | None:
        if not self._samples:
            return None

        return self._samples[-1]

    @property
    def duration_s(self) -> float:
        if len(self._samples) < 2:
            return 0.0

        return (
            self._samples[-1].timestamp_s
            - self._samples[0].timestamp_s
        )

    def values(self) -> tuple[float, ...]:
        return tuple(
            sample.value
            for sample in self._samples
        )

    def _trim(self, current_timestamp_s: float) -> None:
        cutoff_s = current_timestamp_s - self.window_s

        while (
            self._samples
            and self._samples[0].timestamp_s < cutoff_s
        ):
            self._samples.popleft()