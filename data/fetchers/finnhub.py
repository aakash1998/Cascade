"""
data/fetchers/finnhub.py — Finnhub market data fetcher
=======================================================
Finnhub provides real-time stock quotes, forex rates, commodity prices,
and market news. Free tier: 60 calls/minute.

What we fetch:
  - Key stock indices (SPY, QQQ, DIA) as market health proxies
  - Major commodity ETFs (GLD, USO, DBA)
  - Currency pairs (USD/EUR, USD/JPY, USD/CNY)
  - Macro news for the user's query

Usage:
  from data.fetchers.finnhub import fetch_finnhub_data
  data = await fetch_finnhub_data(query="US China trade war")
"""

import asyncio
from typing import Optional

import httpx

from config import settings
from data.cache import cache


FINNHUB_BASE = "https://finnhub.io/api/v1"

# Symbols to always fetch as macro health proxies
WATCH_SYMBOLS = [
    "SPY",    # S&P 500 ETF
    "QQQ",    # NASDAQ ETF
    "GLD",    # Gold ETF
    "USO",    # Oil ETF
    "TLT",    # 20Y Treasury Bond ETF
    "UUP",    # USD Bullish ETF
]


async def _get_quote(client: httpx.AsyncClient, symbol: str) -> tuple[str, Optional[dict]]:
    """Fetches current quote for one symbol."""
    try:
        resp = await client.get(
            f"{FINNHUB_BASE}/quote",
            params={"symbol": symbol, "token": settings.FINNHUB_API_KEY},
            timeout=settings.API_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        # c=current, o=open, h=high, l=low, pc=prev close, dp=%change
        if data.get("c", 0) == 0:
            return symbol, None
        return symbol, {
            "current":     data.get("c"),
            "open":        data.get("o"),
            "high":        data.get("h"),
            "low":         data.get("l"),
            "prev_close":  data.get("pc"),
            "pct_change":  round(data.get("dp", 0), 2),
            "c":           data.get("c"),
            "dp":          data.get("dp", 0),
        }
    except Exception:
        return symbol, None


async def _get_market_news(client: httpx.AsyncClient, category: str = "general") -> list[dict]:
    """Fetches recent market news headlines."""
    try:
        resp = await client.get(
            f"{FINNHUB_BASE}/news",
            params={"category": category, "token": settings.FINNHUB_API_KEY},
            timeout=settings.API_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        items = resp.json()[:6]
        return [
            {
                "headline": item.get("headline", ""),
                "source":   item.get("source", ""),
                "summary":  item.get("summary", "")[:200],
                "url":      item.get("url", ""),
            }
            for item in items
        ]
    except Exception:
        return []


async def fetch_finnhub_data(query: str = "") -> dict:
    """
    Fetches market quotes and news from Finnhub.

    Returns:
      {
        "quotes": {"SPY": {"current": 485.2, "pct_change": 0.34, ...}, ...},
        "news":   [{"headline": ..., "source": ..., "summary": ...}, ...]
      }
    """
    if not settings.FINNHUB_API_KEY:
        return {"quotes": {}, "news": []}

    cache_key = f"finnhub:market:{query[:40]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = {"quotes": {}, "news": []}

    try:
        async with httpx.AsyncClient() as client:
            # Fetch quotes + news in parallel
            quote_tasks = [_get_quote(client, s) for s in WATCH_SYMBOLS]
            news_task   = _get_market_news(client, "general")

            raw = await asyncio.gather(*quote_tasks, news_task, return_exceptions=True)

        # Quotes are first N results
        for item in raw[:-1]:
            if isinstance(item, Exception):
                continue
            symbol, data = item
            if data:
                result["quotes"][symbol] = data

        # News is last item
        news_result = raw[-1]
        if isinstance(news_result, list):
            result["news"] = news_result

    except Exception as e:
        print(f"⚠️  Finnhub fetch error: {e}")

    cache.set(cache_key, result, ttl=300)  # market data: 5 min cache
    return result
