"""
API Usage Tracker for RadBot.

Thread-safe call counter with rolling windows (1 min, 1 hour, 1 day).
Logs periodic summaries to a dedicated api_usage.log file.

Usage:
    from utils.api_tracker import api_tracker
    api_tracker.record('astrolescent')
    api_tracker.record('radix_gateway')
"""

import time
import threading
import logging
from collections import deque
from typing import Dict

logger = logging.getLogger('radbot.api_usage')

# Window durations in seconds
_WINDOW_1MIN = 60
_WINDOW_1HOUR = 3600
_WINDOW_1DAY = 86400

# How often to emit a summary line (seconds)
_SUMMARY_INTERVAL = 60


class ApiTracker:
    """Thread-safe API call counter with rolling time windows."""

    def __init__(self):
        self._lock = threading.Lock()
        # Per-endpoint deque of timestamps
        self._calls: Dict[str, deque] = {}
        # Session-lifetime totals
        self._totals: Dict[str, int] = {}
        # Periodic summary
        self._last_summary_time = time.monotonic()
        self._session_start = time.time()

    def record(self, endpoint: str) -> None:
        """
        Record a single API call for the given endpoint.

        Args:
            endpoint: Logical name, e.g. 'astrolescent', 'radix_gateway'.
        """
        now = time.monotonic()
        with self._lock:
            if endpoint not in self._calls:
                self._calls[endpoint] = deque()
                self._totals[endpoint] = 0
            self._calls[endpoint].append(now)
            self._totals[endpoint] += 1

            # Emit summary if interval elapsed
            if now - self._last_summary_time >= _SUMMARY_INTERVAL:
                self._emit_summary(now)
                self._last_summary_time = now

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get current stats for all endpoints.

        Returns:
            Dict keyed by endpoint, each containing:
                'last_1min', 'last_1hour', 'last_1day', 'session_total'
        """
        now = time.monotonic()
        with self._lock:
            return self._build_stats(now)

    def _build_stats(self, now: float) -> Dict[str, Dict[str, int]]:
        """Build stats dict (caller must hold lock)."""
        stats = {}
        for endpoint, timestamps in self._calls.items():
            # Prune entries older than 1 day
            cutoff_day = now - _WINDOW_1DAY
            while timestamps and timestamps[0] < cutoff_day:
                timestamps.popleft()

            count_1min = sum(1 for t in timestamps if t >= now - _WINDOW_1MIN)
            count_1hour = sum(1 for t in timestamps if t >= now - _WINDOW_1HOUR)
            count_1day = len(timestamps)

            stats[endpoint] = {
                'last_1min': count_1min,
                'last_1hour': count_1hour,
                'last_1day': count_1day,
                'session_total': self._totals.get(endpoint, 0),
            }
        return stats

    def _emit_summary(self, now: float) -> None:
        """Log a summary line (caller must hold lock)."""
        stats = self._build_stats(now)
        if not stats:
            return

        parts_1min = []
        parts_1hour = []
        parts_1day = []
        parts_total = []

        for endpoint in sorted(stats):
            s = stats[endpoint]
            parts_1min.append(f"{endpoint}={s['last_1min']}")
            parts_1hour.append(f"{endpoint}={s['last_1hour']}")
            parts_1day.append(f"{endpoint}={s['last_1day']}")
            parts_total.append(f"{endpoint}={s['session_total']}")

        uptime_mins = (time.time() - self._session_start) / 60

        logger.info(
            f"API calls (1m): {', '.join(parts_1min)} | "
            f"(1h): {', '.join(parts_1hour)} | "
            f"(1d): {', '.join(parts_1day)} | "
            f"Session totals: {', '.join(parts_total)} | "
            f"Uptime: {uptime_mins:.0f}min"
        )


# Module-level singleton
api_tracker = ApiTracker()
