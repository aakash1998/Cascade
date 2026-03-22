"""
data/cache.py — In-memory TTL cache for API responses
======================================================
Prevents hammering the same API endpoint twice in one session.
Every data fetcher checks this cache before making a network call.

How it works:
  1. Fetcher calls cache.get(key) — returns None if miss or expired
  2. On a miss, fetcher makes the real API call
  3. Fetcher calls cache.set(key, data) to store the result
  4. Next call within TTL seconds gets data instantly from cache

Why this matters:
  - Multiple domain agents need the same FRED data
  - Without caching, we'd hit the same endpoint 10+ times per query
  - With caching, we hit it once and reuse the result for all agents

Usage:
  from data.cache import cache

  data = cache.get("fred:UNRATE")
  if data is None:
      data = await fetch_fred_unemployment()
      cache.set("fred:UNRATE", data)
"""

import time
from typing import Any, Optional

from config import settings


class _CacheEntry:
    """One item stored in the cache with an expiry timestamp."""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.monotonic() + ttl

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class TTLCache:
    """
    In-memory key-value cache where each entry expires after `ttl` seconds.

    Not thread-safe — fine for asyncio (single-threaded event loop).
    No size cap — sessions are short so memory growth is bounded.
    """

    def __init__(self, default_ttl: int = None):
        self._store: dict = {}
        self._default_ttl = default_ttl or settings.CACHE_TTL_SECONDS

    def get(self, key: str) -> Optional[Any]:
        """
        Returns the cached value, or None if absent / expired.

        Example:
            val = cache.get("fred:UNRATE")
            if val is None:
                val = await actually_fetch()
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        Stores value under key for ttl seconds (default: CACHE_TTL_SECONDS).

        Example:
            cache.set("fred:UNRATE", {"value": 4.1})
            cache.set("tavily:trade", [...], ttl=1800)
        """
        self._store[key] = _CacheEntry(value, ttl or self._default_ttl)

    def delete(self, key: str) -> None:
        """Evicts a specific entry."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Removes all entries."""
        self._store.clear()

    def purge_expired(self) -> int:
        """Removes expired entries and returns the count removed."""
        expired = [k for k, e in self._store.items() if e.is_expired()]
        for k in expired:
            del self._store[k]
        return len(expired)

    def size(self) -> int:
        """Returns the number of live (non-expired) entries."""
        self.purge_expired()
        return len(self._store)

    def stats(self) -> dict:
        """Returns cache statistics for the /health endpoint."""
        return {
            "active_entries": self.size(),
            "default_ttl_sec": self._default_ttl,
        }


# ─────────────────────────────────────────────
# SINGLETON — one shared cache for the whole process
# ─────────────────────────────────────────────

cache = TTLCache()
