"""Source health tracking — circuit breaker pattern.

If a source fails N consecutive times, auto-disable it for the current run
and flag it in the health table instead of retrying indefinitely.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class SourceHealth:
    """Health record for a single source."""
    name: str
    consecutive_failures: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    is_disabled: bool = False
    total_items: int = 0

    @property
    def is_healthy(self) -> bool:
        return not self.is_disabled


class SourceHealthTracker:
    """Track health of all sources — circuit breaker for flaky ones."""

    def __init__(self, failure_threshold: int = 3, state_path: str | None = None):
        """
        Args:
            failure_threshold: Consecutive failures before disabling a source
            state_path: Path to JSON file for persisting health state
        """
        self.failure_threshold = failure_threshold
        self.state_path = state_path
        self._sources: dict[str, SourceHealth] = {}

    def get_or_create(self, source_name: str) -> SourceHealth:
        """Get or create health record for a source."""
        if source_name not in self._sources:
            self._sources[source_name] = SourceHealth(name=source_name)
        return self._sources[source_name]

    def is_source_enabled(self, source_name: str) -> bool:
        """Check if a source is currently enabled (not circuit-broken)."""
        source = self.get_or_create(source_name)
        return source.is_healthy

    def record_success(self, source_name: str, item_count: int = 0) -> None:
        """Record a successful fetch — resets failure counter."""
        source = self.get_or_create(source_name)
        source.consecutive_failures = 0
        source.last_success = datetime.now(timezone.utc)
        source.is_disabled = False
        source.total_items += item_count
        logger.info(f"Source {source_name}: OK ({item_count} items)")

    def record_failure(self, source_name: str, error: str | None = None) -> bool:
        """
        Record a failed fetch.

        Returns:
            True if source is now disabled (circuit broken)
        """
        source = self.get_or_create(source_name)
        source.consecutive_failures += 1
        source.last_failure = datetime.now(timezone.utc)

        if source.consecutive_failures >= self.failure_threshold:
            source.is_disabled = True
            logger.warning(
                f"Source {source_name}: CIRCUIT BROKEN after "
                f"{source.consecutive_failures} consecutive failures. "
                f"Last error: {error}"
            )
            return True

        logger.warning(
            f"Source {source_name}: failure {source.consecutive_failures}/"
            f"{self.failure_threshold}"
        )
        return False

    def get_health_table(self) -> list[dict[str, Any]]:
        """Get health status for all sources — for display/reporting."""
        table = []
        for source in self._sources.values():
            table.append({
                "source": source.name,
                "status": "disabled" if source.is_disabled else "healthy",
                "consecutive_failures": source.consecutive_failures,
                "last_success": source.last_success.isoformat() if source.last_success else None,
                "last_failure": source.last_failure.isoformat() if source.last_failure else None,
                "total_items": source.total_items,
            })

        # Sort: disabled first, then by most failures
        table.sort(key=lambda x: (x["status"] != "disabled", x["consecutive_failures"]), reverse=True)
        return table

    def get_disabled_sources(self) -> list[str]:
        """Get list of currently disabled source names."""
        return [s.name for s in self._sources.values() if s.is_disabled]

    def get_healthy_sources(self) -> list[str]:
        """Get list of currently healthy source names."""
        return [s.name for s in self._sources.values() if s.is_healthy]

    def reset_source(self, source_name: str) -> None:
        """Reset failure count for a source (e.g., after manual intervention)."""
        source = self.get_or_create(source_name)
        source.consecutive_failures = 0
        source.is_disabled = False
        logger.info(f"Source {source_name}: manually reset")

    def reset_all(self) -> None:
        """Reset all sources to healthy."""
        for source in self._sources.values():
            source.consecutive_failures = 0
            source.is_disabled = False
        logger.info("All sources reset to healthy")
