"""
data/fetchers/gdelt.py — GDELT global event database fetcher
=============================================================
GDELT (Global Database of Events, Language, and Tone) monitors
world news in near real-time and assigns tone/sentiment scores.
It's completely free with no API key needed.

What it gives us:
  - Real-time article headlines from thousands of news sources
  - Tone score: negative = bad news, positive = good news
  - Country and actor codes for geographic context
  - Great for detecting sentiment shifts around world events

API: GDELT 2.0 GKG API via their public endpoint

Usage:
  from data.fetchers.gdelt import fetch_gdelt_events
  events = await fetch_gdelt_events("US China tariffs trade war")
"""

import asyncio
from typing import Optional
from urllib.parse import quote

import httpx

from config import settings
from data.cache import cache


GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


async def fetch_gdelt_events(query: str, max_results: int = 15) -> list[dict]:
    """
    Searches GDELT for recent articles matching the query.
    Returns articles with tone scores and metadata.

    Args:
        query:       The topic to search for
        max_results: Maximum number of articles to return

    Returns:
        List of dicts:
          [
            {
              "title":       Article title,
              "url":         Article URL,
              "domain":      Source domain,
              "language":    Language code,
              "tone":        Sentiment score (negative = bad),
              "date":        Publication date string,
            },
            ...
          ]
    """
    cache_key = f"gdelt:{query[:80]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        "query":     query,
        "mode":      "artlist",
        "maxrecords": min(max_results, 25),
        "format":    "json",
        "timespan":  "2weeks",       # last 2 weeks of coverage
        "sort":      "DateDesc",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GDELT_API_URL,
                params=params,
                timeout=settings.API_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()

        articles = data.get("articles", [])
        results = []
        for art in articles:
            tone = None
            try:
                tone = float(art.get("tone", 0))
            except (ValueError, TypeError):
                pass

            results.append({
                "title":    art.get("title", ""),
                "url":      art.get("url", ""),
                "domain":   art.get("domain", ""),
                "language": art.get("language", "English"),
                "tone":     tone,
                "date":     art.get("seendate", "")[:14],  # YYYYMMDDHHMMSS format
            })

        cache.set(cache_key, results)
        return results

    except asyncio.TimeoutError:
        print(f"⏱️  GDELT timed out for query: {query[:50]}")
        return []
    except Exception as e:
        print(f"⚠️  GDELT fetch failed: {e}")
        return []
