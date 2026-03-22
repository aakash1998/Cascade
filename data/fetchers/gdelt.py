"""
data/fetchers/gdelt.py — GDELT World Events Fetcher
=====================================================
GDELT (Global Database of Events, Language, and Tone) monitors
the world's news media in 100+ languages and updates every 15
minutes. It is the most comprehensive free source of world
event data available anywhere.

What it provides:
  - Every significant world event logged as structured data
  - Conflict events, protests, diplomatic meetings, disasters
  - Tone/sentiment of news coverage per country per topic
  - Updated every 15 minutes — near real-time
  - Completely free, no API key needed

How Cascade uses it:
  The Geopolitics, Social, and Migration agents use GDELT to
  ground their analysis in actual events happening right now,
  not just LLM training knowledge.

GDELT API endpoints we use:
  DOC API — search articles by keyword, returns recent news
  GEO API — events filtered by geography

Usage:
  from data.fetchers.gdelt import fetch_gdelt_events

  events = await fetch_gdelt_events("Russia Ukraine conflict")
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import httpx
from config import settings
from data.cache import cache


GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


async def fetch_gdelt_events(
    query:     str,
    max_items: int = 10,
    cache_ttl: int = 900,    # 15 min — GDELT updates every 15 min
) -> list[dict]:
    """
    Searches GDELT for recent news articles matching a query.
    Returns structured article data with tone/sentiment scores.

    Args:
        query:     Search terms
        max_items: Max articles to return
        cache_ttl: Cache duration in seconds (default 15 min)

    Returns:
        List of article dicts:
        {
          "title":    "Article headline",
          "url":      "https://...",
          "source":   "Reuters",
          "date":     "20251101120000",
          "tone":     -3.5,   # negative = bad news, positive = good
          "country":  "US",
        }
    """
    cache_key = f"gdelt:{query[:60]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "query":    query,
            "mode":     "ArtList",
            "maxrecords": max_items,
            "format":   "json",
            "sort":     "DateDesc",   # newest first
        }

        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            response = await client.get(GDELT_DOC_API, params=params)
            response.raise_for_status()
            data = response.json()

        articles = data.get("articles", [])

        normalised = []
        for article in articles:
            normalised.append({
                "title":   article.get("title", ""),
                "url":     article.get("url", ""),
                "source":  article.get("domain", ""),
                "date":    article.get("seendate", ""),
                "tone":    float(article.get("tone", 0)),
                "country": article.get("sourcecountry", ""),
                "source_label": "GDELT",
            })

        cache.set(cache_key, normalised, ttl=cache_ttl)
        return normalised

    except Exception as e:
        print(f"⚠️  GDELT fetch failed for '{query[:40]}': {e}")
        return []


async def fetch_gdelt_tone(query: str) -> dict:
    """
    Fetches the average news tone for a topic.
    Tone ranges from very negative (-10) to very positive (+10).
    Useful as a sentiment signal for the Social and Geopolitics agents.

    Returns:
        { "tone": -3.5, "volume": 142, "interpretation": "negative" }
    """
    cache_key = f"gdelt:tone:{query[:60]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "query":  query,
            "mode":   "ToneChart",
            "format": "json",
        }

        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            response = await client.get(GDELT_DOC_API, params=params)
            response.raise_for_status()
            data = response.json()

        # Extract average tone from response
        tone_data = data.get("tonetrendline", [])
        if tone_data:
            avg_tone = sum(t.get("avgtone", 0) for t in tone_data) / len(tone_data)
        else:
            avg_tone = 0.0

        result = {
            "tone":           round(avg_tone, 2),
            "volume":         len(tone_data),
            "interpretation": "negative" if avg_tone < -2 else "positive" if avg_tone > 2 else "neutral",
            "source":         "GDELT",
        }

        cache.set(cache_key, result, ttl=900)
        return result

    except Exception as e:
        print(f"⚠️  GDELT tone fetch failed: {e}")
        return {"tone": 0.0, "volume": 0, "interpretation": "unknown"}


if __name__ == "__main__":
    async def test():
        print("\n🧪 Testing GDELT fetcher...\n")

        events = await fetch_gdelt_events("US China trade war tariffs", max_items=5)

        if events:
            print(f"✅ GDELT returned {len(events)} events\n")
            for e in events[:3]:
                print(f"  - {e['title'][:70]}")
                print(f"    Source: {e['source']} | Tone: {e['tone']:.1f}\n")
        else:
            print("⚠️  No GDELT results — API may be rate limited, try again")

        tone = await fetch_gdelt_tone("inflation recession")
        print(f"✅ Tone for 'inflation recession': {tone['tone']} ({tone['interpretation']})\n")

    asyncio.run(test())