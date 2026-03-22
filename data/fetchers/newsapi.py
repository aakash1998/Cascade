"""
data/fetchers/newsapi.py — NewsAPI.org headline fetcher
========================================================
NewsAPI provides headlines from 80,000+ news sources.
Free tier: 100 requests/day, last 30 days of archives.

We use it as a backup news source to complement Tavily.
While Tavily gives rich summarized content, NewsAPI gives
us breadth — more sources, more headlines.

API: https://newsapi.org/v2/everything

Usage:
  from data.fetchers.newsapi import fetch_newsapi_headlines
  articles = await fetch_newsapi_headlines("Federal Reserve interest rates")
"""

import asyncio
from typing import Optional

import httpx

from config import settings
from data.cache import cache


NEWSAPI_URL = "https://newsapi.org/v2/everything"


async def fetch_newsapi_headlines(query: str, max_results: int = 8) -> list[dict]:
    """
    Fetches recent news headlines from NewsAPI.

    Args:
        query:       Search query
        max_results: Number of articles to return (max 100)

    Returns:
        List of article dicts:
          [
            {
              "title":       Article title,
              "description": Article description,
              "source":      {"name": "Reuters"},
              "url":         Article URL,
              "publishedAt": ISO date string,
              "author":      Author name (if available),
            },
            ...
          ]
        Returns empty list if API key missing or request fails.
    """
    if not settings.TAVILY_API_KEY:  # NewsAPI key stored separately but optional
        return []

    # Use NEWSAPI_KEY from env if available, otherwise skip
    import os
    newsapi_key = os.getenv("NEWSAPI_KEY", "").strip()
    if not newsapi_key:
        return []

    cache_key = f"newsapi:{query[:80]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        "q":          query,
        "apiKey":     newsapi_key,
        "language":   "en",
        "sortBy":     "relevancy",
        "pageSize":   min(max_results, 20),
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                NEWSAPI_URL,
                params=params,
                timeout=settings.API_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()

        articles = data.get("articles", [])
        results = [
            {
                "title":       art.get("title", ""),
                "description": art.get("description", ""),
                "source":      art.get("source", {}),
                "url":         art.get("url", ""),
                "publishedAt": art.get("publishedAt", ""),
                "author":      art.get("author", ""),
            }
            for art in articles
            if art.get("title") and "[Removed]" not in art.get("title", "")
        ]

        cache.set(cache_key, results)
        return results

    except asyncio.TimeoutError:
        print(f"⏱️  NewsAPI timed out for query: {query[:50]}")
        return []
    except Exception as e:
        print(f"⚠️  NewsAPI fetch failed: {e}")
        return []
