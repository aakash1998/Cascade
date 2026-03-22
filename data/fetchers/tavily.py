"""
data/fetchers/tavily.py — Tavily web search fetcher
====================================================
Tavily is an AI-powered search API designed specifically for LLMs.
It returns clean, summarized results — no HTML scraping needed.

Why Tavily:
  - Purpose-built for RAG (retrieval augmented generation)
  - Returns pre-summarized snippets, not raw HTML
  - Replaces 15+ individual news APIs with one call
  - Free tier: 1000 searches/month

Used by Scout to get current news and web context for any query.

Usage:
  from data.fetchers.tavily import fetch_tavily
  results = await fetch_tavily("US China trade war impact on tech sector")
"""

import asyncio
from typing import Optional

from config import settings
from data.cache import cache


async def fetch_tavily(
    query: str,
    max_results: int = None,
    search_depth: str = "advanced",
) -> list[dict]:
    """
    Searches the web via Tavily and returns structured results.

    Args:
        query:        The search query
        max_results:  How many results to return (default from settings)
        search_depth: "basic" (fast) or "advanced" (more thorough, same cost)

    Returns:
        List of dicts, each with:
          - title:          Article title
          - content:        Summarized content snippet
          - url:            Original URL
          - published_date: ISO date string (if available)
          - score:          Relevance score 0.0-1.0

        Returns empty list if API key missing or request fails.
    """
    if not settings.TAVILY_API_KEY:
        return []

    # Check cache first
    cache_key = f"tavily:{query[:100]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

        n = max_results or settings.TAVILY_MAX_RESULTS
        response = await asyncio.wait_for(
            client.search(
                query=query,
                max_results=n,
                search_depth=search_depth,
                include_raw_content=False,
            ),
            timeout=settings.API_TIMEOUT_SECONDS,
        )

        results = response.get("results", [])
        # Normalize field names — Tavily returns slightly different shapes
        normalized = [
            {
                "title":          r.get("title", ""),
                "content":        r.get("content", ""),
                "url":            r.get("url", ""),
                "published_date": r.get("published_date", ""),
                "score":          r.get("score", 0.5),
            }
            for r in results
        ]

        cache.set(cache_key, normalized)
        return normalized

    except asyncio.TimeoutError:
        print(f"⏱️  Tavily timed out for query: {query[:50]}")
        return []
    except Exception as e:
        print(f"⚠️  Tavily fetch failed: {e}")
        return []
