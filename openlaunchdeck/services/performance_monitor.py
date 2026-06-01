from __future__ import annotations

import logging
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass(frozen=True, slots=True)
class PerformanceSample:
    label: str
    elapsed_ms: float
    timestamp: float
    details: dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    def __init__(self, logger=None, enabled: bool = False, max_samples: int = 256) -> None:
        self.logger = logger
        self.enabled = enabled
        self._samples: deque[PerformanceSample] = deque(maxlen=max_samples)

    @staticmethod
    def now() -> float:
        return time.perf_counter()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def mark(self, label: str, **details: Any) -> None:
        self.record(label, 0.0, **details)

    def record_since(self, label: str, start: float, **details: Any) -> float:
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.record(label, elapsed_ms, **details)
        return elapsed_ms

    def record(self, label: str, elapsed_ms: float, **details: Any) -> None:
        if not self.enabled and not self._debug_logging_enabled():
            return
        sample = PerformanceSample(
            label=label,
            elapsed_ms=elapsed_ms,
            timestamp=time.time(),
            details=dict(details),
        )
        if self.enabled:
            self._samples.append(sample)
        self._log(sample)

    def samples(self) -> list[PerformanceSample]:
        return list(self._samples)

    @contextmanager
    def measure(self, label: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.record_since(label, start)

    def _log(self, sample: PerformanceSample) -> None:
        if not self.logger:
            return
        if self.enabled:
            log_enabled = self.logger.isEnabledFor(logging.INFO)
        else:
            log_enabled = self.logger.isEnabledFor(logging.DEBUG)
        if not log_enabled:
            return
        details = ""
        if sample.details:
            details = " " + " ".join(f"{key}={value}" for key, value in sample.details.items())
        if self.enabled:
            self.logger.info("Performance %s: %.3f ms%s", sample.label, sample.elapsed_ms, details)
        else:
            self.logger.debug("Performance %s: %.3f ms%s", sample.label, sample.elapsed_ms, details)

    def _debug_logging_enabled(self) -> bool:
        return bool(self.logger and self.logger.isEnabledFor(logging.DEBUG))
