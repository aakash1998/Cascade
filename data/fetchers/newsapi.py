"""
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

data/fetchers/newsapi.py — NewsAPI News Fetcher
NewsAPI aggregates headlines from 150,000+ news sources
worldwide. Useful as a secondary news source alongside Tavily.

Free tier: 100 requests/day, 30 days history.

When to use NewsAPI vs Tavily:
  Tavily  = general web search, best for deep topic research
  NewsAPI = structured news headlines, good for quick current
            events pulse across specific categories

Categories available:
  business, entertainment, general, health,
  science, sports, technology

Usage:
  from data.fetchers.newsapi import fetch_top_headlines, fetch_news_search

  headlines = await fetch_top_headlines(category="business")
  results   = await fetch_news_search("US China trade war")
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import httpx
from config import settings
from data.cache import cache


NEWSAPI_BASE = "https://newsapi.org/v2"


async def fetch_top_headlines(
    category:  str = "general",
    country:   str = "us",
    max_items: int = 10,
    cache_ttl: int = 1800,   # 30 min
) -> list[dict]:
    """
    Fetches top headlines for a given category.

    Args:
        category:  One of: business, entertainment, general,
                   health, science, sports, technology
        country:   2-letter country code (us, gb, ca, au, etc.)
        max_items: Max headlines to return

    Returns:
        List of headline dicts with title, description, source, url
    """
    if not settings.NEWS_API_KEY:
        return []

    cache_key = f"newsapi:headlines:{category}:{country}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "apiKey":   settings.NEWS_API_KEY,
            "category": category,
            "country":  country,
            "pageSize": max_items,
        }

        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{NEWSAPI_BASE}/top-headlines", params=params)
            response.raise_for_status()
            data = response.json()

        articles = data.get("articles", [])

        normalised = [
            {
                "title":       a.get("title", ""),
                "description": a.get("description", "")[:200] if a.get("description") else "",
                "source":      a.get("source", {}).get("name", ""),
                "url":         a.get("url", ""),
                "published":   a.get("publishedAt", ""),
                "source_label":"NewsAPI",
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]

        cache.set(cache_key, normalised, ttl=cache_ttl)
        return normalised

    except Exception as e:
        print(f"⚠️  NewsAPI headlines failed ({category}): {e}")
        return []


async def fetch_news_search(
    query:     str,
    max_items: int = 10,
    cache_ttl: int = 1800,
) -> list[dict]:
    """
    Searches NewsAPI for articles matching a query.
    Searches article titles, descriptions, and content.

    Args:
        query:     Search terms
        max_items: Max articles to return

    Returns:
        List of article dicts
    """
    if not settings.NEWS_API_KEY:
        return []

    cache_key = f"newsapi:search:{query[:60]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "apiKey":   settings.NEWS_API_KEY,
            "q":        query,
            "pageSize": max_items,
            "sortBy":   "relevancy",
            "language": "en",
        }

        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{NEWSAPI_BASE}/everything", params=params)
            response.raise_for_status()
            data = response.json()

        articles = data.get("articles", [])

        normalised = [
            {
                "title":       a.get("title", ""),
                "description": a.get("description", "")[:200] if a.get("description") else "",
                "source":      a.get("source", {}).get("name", ""),
                "url":         a.get("url", ""),
                "published":   a.get("publishedAt", ""),
                "source_label":"NewsAPI",
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]

        cache.set(cache_key, normalised, ttl=cache_ttl)
        return normalised

    except Exception as e:
        print(f"⚠️  NewsAPI search failed for '{query[:40]}': {e}")
        return []


async def fetch_newsapi_snapshot(query: str) -> dict:
    """
    Fetches both business headlines and query-specific news.
    Called by Scout for the full data context.

    Returns:
        {
          "business_headlines": [...],
          "query_articles":     [...],
          "source": "NewsAPI"
        }
    """
    cache_key = f"newsapi:snapshot:{query[:60]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    business, articles = await asyncio.gather(
        fetch_top_headlines(category="business", max_items=5),
        fetch_news_search(query, max_items=5),
        return_exceptions=True,
    )

    snapshot = {
        "business_headlines": business if not isinstance(business, Exception) else [],
        "query_articles":     articles if not isinstance(articles, Exception) else [],
        "source":             "NewsAPI",
    }

    cache.set(cache_key, snapshot, ttl=1800)
    return snapshot


if __name__ == "__main__":
    async def test():
        print("\n🧪 Testing NewsAPI fetcher...\n")

        if not settings.NEWS_API_KEY:
            print("⚠️  NEWS_API_KEY not set in .env — skipping test")
            return

        # Test search
        print("Searching for 'trade war tariffs'...")
        results = await fetch_news_search("trade war tariffs", max_items=3)

        if results:
            print(f"✅ NewsAPI returned {len(results)} articles\n")
            for r in results:
                print(f"  - {r['title'][:70]}")
                print(f"    Source: {r['source']} | {r['published'][:10]}\n")
        else:
            print("⚠️  No results — check NEWS_API_KEY or daily limit")

        # Test headlines
        print("Fetching business headlines...")
        headlines = await fetch_top_headlines(category="business", max_items=3)
        if headlines:
            print(f"✅ {len(headlines)} business headlines\n")
            for h in headlines:
                print(f"  - {h['title'][:70]}")
        print()

    asyncio.run(test())
