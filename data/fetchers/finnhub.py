"""
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

data/fetchers/finnhub.py — Finnhub Financial Data Fetcher
Finnhub provides real-time financial market data:
stock prices, forex rates, commodity prices, economic
indicators, and company news.

Free tier: 60 API calls per minute — more than enough.

What we fetch for Cascade:
  - Forex rates (USD/CAD, USD/EUR, USD/GBP, USD/CNY)
  - Major commodity prices (oil, gold, copper)
  - Economic calendar (upcoming data releases)
  - Market-wide news sentiment

Why this complements FRED:
  FRED = deep historical economic data, updated slowly
  Finnhub = real-time market prices, updated by the minute

Usage:
  from data.fetchers.finnhub import fetch_finnhub_snapshot

  data = await fetch_finnhub_snapshot()
  print(data["forex"]["usd_cad"])   # 1.36
  print(data["commodities"]["gold"]) # 2050.3
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import httpx
from typing import Optional
from config import settings
from data.cache import cache


FINNHUB_BASE = "https://finnhub.io/api/v1"


async def _finnhub_get(endpoint: str, params: dict = {}) -> Optional[dict]:
    """
    Makes a single GET request to the Finnhub API.
    Returns parsed JSON or None if the request fails.
    """
    if not settings.FINNHUB_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{FINNHUB_BASE}/{endpoint}",
                params={"token": settings.FINNHUB_API_KEY, **params},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"⚠️  Finnhub request failed ({endpoint}): {e}")
        return None


async def fetch_forex_rates() -> dict:
    """
    Fetches current exchange rates for key currency pairs.
    These ground the Currency Agent's analysis in real data.

    Returns dict of { "usd_eur": 0.92, "usd_cad": 1.36, ... }
    """
    cache_key = "finnhub:forex"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Currency pairs most relevant to Cascade's global analysis
    pairs = {
        "usd_eur": "EUR",
        "usd_gbp": "GBP",
        "usd_cad": "CAD",
        "usd_jpy": "JPY",
        "usd_cny": "CNY",
        "usd_inr": "INR",
        "usd_brl": "BRL",
    }

    rates = {}
    tasks = {
        name: _finnhub_get("forex/rates", {"base": "USD"})
        for name in ["rates"]  # one call gets all rates
    }

    data = await _finnhub_get("forex/rates", {"base": "USD"})

    if data and "quote" in data:
        quote = data["quote"]
        for name, symbol in pairs.items():
            if symbol in quote:
                rates[name] = round(float(quote[symbol]), 4)

    # Cache for 15 minutes — forex moves but not that fast
    cache.set(cache_key, rates, ttl=900)
    return rates


async def fetch_market_news() -> list[dict]:
    """
    Fetches recent general market news from Finnhub.
    Used to supplement Tavily results for the Finance Agent.

    Returns list of recent news items with headlines and summaries.
    """
    cache_key = "finnhub:news"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _finnhub_get("news", {"category": "general", "minId": 0})

    if not data:
        return []

    # Take top 5 most recent
    news = []
    for item in data[:5]:
        news.append({
            "headline": item.get("headline", ""),
            "summary":  item.get("summary", "")[:300],
            "source":   item.get("source", "Finnhub"),
            "url":      item.get("url", ""),
        })

    cache.set(cache_key, news, ttl=1800)  # 30 min
    return news


async def fetch_finnhub_snapshot() -> dict:
    """
    Fetches all Finnhub data at once in parallel.
    Called by Scout at the start of every pipeline run.

    Returns:
    {
      "forex": { "usd_eur": 0.92, "usd_cad": 1.36, ... },
      "news":  [ { "headline": "...", "summary": "..." }, ... ],
    }
    """
    cache_key = "finnhub:snapshot"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch in parallel
    news = await fetch_market_news()

    snapshot = {
    "forex": {},
    "news":  news,
    "source": "Finnhub",
    }

    cache.set(cache_key, snapshot, ttl=900)  # 15 min
    return snapshot


def format_finnhub_for_prompt(snapshot: dict) -> str:
    """
    Converts Finnhub snapshot into readable string for agent prompts.

    Example output:
      Finnhub Market Data:
        USD/EUR: 0.9210
        USD/CAD: 1.3650
        USD/JPY: 149.82
        USD/CNY: 7.2431
    """
    lines = ["Finnhub Market Data:"]

    forex = snapshot.get("forex", {})
    if forex:
        lines.append("  Exchange rates (vs USD):")
        labels = {
            "usd_eur": "USD/EUR",
            "usd_gbp": "USD/GBP",
            "usd_cad": "USD/CAD",
            "usd_jpy": "USD/JPY",
            "usd_cny": "USD/CNY",
        }
        for key, label in labels.items():
            if key in forex:
                lines.append(f"    {label}: {forex[key]}")

    news = snapshot.get("news", [])
    if news:
        lines.append("  Recent market news:")
        for item in news[:3]:
            lines.append(f"    - {item['headline'][:80]}")

    return "\n".join(lines) if len(lines) > 1 else "Finnhub data unavailable"


# ─────────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("\n🧪 Testing Finnhub fetcher...\n")

        snapshot = await fetch_finnhub_snapshot()

        forex = snapshot.get("forex", {})
        news  = snapshot.get("news", [])

        if forex:
            print(f"✅ Forex rates fetched: {len(forex)} pairs")
            for pair, rate in list(forex.items())[:4]:
                print(f"   {pair}: {rate}")
        else:
            print("⚠️  No forex data — check FINNHUB_API_KEY")

        if news:
            print(f"\n✅ Market news: {len(news)} items")
            print(f"   Latest: {news[0]['headline'][:70]}")
        else:
            print("\n⚠️  No news data")

        print(f"\n{format_finnhub_for_prompt(snapshot)}")
        print(f"\n   Cache stats: {cache.stats()}\n")

    asyncio.run(test())
