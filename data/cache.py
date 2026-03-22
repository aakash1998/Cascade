"""
data/cache.py — Simple in-memory TTL cache
============================================
Prevents hammering the same API twice in one session.
Every fetcher checks this cache before making a network call.

How it works:
  - Every API response is stored with a timestamp
  - On next request for same key, if timestamp is within TTL → return cached
  - If TTL expired → fetch fresh data, update cache
  - Cache lives in RAM — resets when app restarts (by design)

Why this matters for cost:
  If 10 users ask about the US-China trade war in the same hour,
  Tavily is only called once. The other 9 get the cached result instantly.
  Saves tokens, saves money, saves time.

Usage:
  from data.cache import cache

  cache.set("fred_cpi", {"value": 3.2}, ttl=3600)
  data = cache.get("fred_cpi")   # returns None if expired
"""

import time
from typing import Any, Optional


class TTLCache:
    """
    Simple in-memory key-value cache with per-entry TTL.
    Thread-safe enough for single-process async use.
    """

    def __init__(self):
        # { key: {"value": ..., "expires_at": float} }
        self._store: dict = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Returns cached value if it exists and hasn't expired.
        Returns None if missing or expired.
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Stores a value with a TTL in seconds.
        Default TTL: 1 hour (3600 seconds)
        """
        self._store[key] = {
            "value":      value,
            "expires_at": time.time() + ttl,
        }

    def delete(self, key: str) -> None:
        """Removes a key from cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clears entire cache — useful for testing."""
        self._store.clear()

    def size(self) -> int:
        """Returns number of non-expired entries."""
        now = time.time()
        return sum(1 for e in self._store.values() if e["expires_at"] > now)

    def stats(self) -> dict:
        """Returns cache stats for debugging."""
        now = time.time()
        total   = len(self._store)
        active  = sum(1 for e in self._store.values() if e["expires_at"] > now)
        expired = total - active
        return {"total": total, "active": active, "expired": expired}


# Global cache instance — shared across all fetchers
cache = TTLCache()