"""
FRED (Federal Reserve Economic Data) provides 800,000+ free economic
time series from the US Federal Reserve. No API key required for
basic access (key unlocks higher rate limits).

Key indicators we fetch:
  UNRATE    — Unemployment rate
  CPIAUCSL  — Consumer Price Index (inflation)
  GDP       — US GDP growth
  FEDFUNDS  — Federal funds rate (interest rates)
  DXY       — US Dollar index (via DTWEXBGS)
  T10Y2Y    — Yield curve (recession indicator)
  MORTGAGE30US — 30-year mortgage rate

Usage:
  from data.fetchers.fred import fetch_fred_indicators
  data = await fetch_fred_indicators()
"""

import asyncio
from typing import Optional

import httpx

data/fetchers/fred.py — FRED Economic Data Fetcher
FRED (Federal Reserve Economic Data) is the most comprehensive
free source of economic data in the world.

What it provides:
  - 800,000+ economic time series
  - US and global indicators
  - Updated daily/weekly/monthly depending on series
  - No key required for basic access (key increases rate limits)

Key series we fetch for Cascade:
  CPIAUCSL  — Consumer Price Index (inflation)
  UNRATE    — US Unemployment Rate
  GDP       — US Gross Domestic Product
  FEDFUNDS  — Federal Funds Rate (interest rates)
  DCOILWTICO — Crude Oil Price (WTI)
  DEXUSEU   — USD/EUR Exchange Rate
  T10YIE    — 10-Year Breakeven Inflation Rate
  UMCSENT   — University of Michigan Consumer Sentiment

Why this matters for agents:
  Agents grounded in real economic data make much better
  predictions than agents reasoning from training data alone.
  When the Labour Agent knows current unemployment is 4.1%,
  its analysis is specific and credible.

Usage:
  from data.fetchers.fred import fetch_fred_series, fetch_fred_snapshot

  # Get one series
  cpi = await fetch_fred_series("CPIAUCSL", limit=12)

  # Get full economic snapshot (all key series at once)
  snapshot = await fetch_fred_snapshot()
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import httpx
from typing import Optional
from config import settings
from data.cache import cache


# Key economic series to fetch for the snapshot
# Format: { "friendly_name": "FRED_series_id" }
KEY_SERIES = {
    "cpi_inflation":      "CPIAUCSL",    # Consumer Price Index
    "unemployment_rate":  "UNRATE",      # US Unemployment Rate
    "gdp_growth":         "A191RL1Q225SBEA",  # Real GDP Growth Rate
    "interest_rate":      "FEDFUNDS",    # Federal Funds Rate
    "oil_price_wti":      "DCOILWTICO",  # Crude Oil Price WTI
    "usd_eur_rate":       "DEXUSEU",     # USD to EUR
    "consumer_sentiment": "UMCSENT",     # Consumer Sentiment
    "inflation_expectation": "T10YIE",   # 10-Year Breakeven Inflation
    "sp500":              "SP500",       # S&P 500 Index
    "housing_starts":     "HOUST",       # Housing Starts
}

FRED_BASE_URL = "https://api.stlouisfed.org/fred"


async def fetch_fred_series(
    series_id: str,
    limit:     int = 6,       # last 6 data points
    cache_ttl: int = 3600,    # 1 hour
) -> Optional[dict]:
    """
    Fetches the most recent observations for one FRED series.

    Args:
        series_id: The FRED series identifier (e.g. "CPIAUCSL")
        limit:     How many recent data points to return
        cache_ttl: Cache duration in seconds

    Returns:
        Dict with series info and recent values, or None if failed.
        {
          "series_id": "CPIAUCSL",
          "name": "Consumer Price Index",
          "latest_value": 314.5,
          "latest_date": "2025-10-01",
          "unit": "Index 1982-1984=100",
          "recent_values": [{"date": "...", "value": 314.5}, ...]
        }
    """
    cache_key = f"fred:{series_id}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "series_id":      series_id,
            "limit":          limit,
            "sort_order":     "desc",
            "file_type":      "json",
        }

        # Add API key if available (increases rate limits)
        if settings.FRED_API_KEY:
            params["api_key"] = settings.FRED_API_KEY
        else:
            # Without a key, FRED still works but rate-limits more aggressively
            params["api_key"] = "abcdefghijklmnopqrstuvwxyz123456"  # demo key

        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            # Fetch observations
            obs_resp = await client.get(
                f"{FRED_BASE_URL}/series/observations",
                params=params,
            )
            obs_resp.raise_for_status()
            obs_data = obs_resp.json()

        observations = obs_data.get("observations", [])

        if not observations:
            return None

        # Parse into clean format
        recent_values = []
        for obs in observations:
            try:
                val = float(obs["value"])
                recent_values.append({
                    "date":  obs["date"],
                    "value": val,
                })
            except (ValueError, KeyError):
                continue  # Skip missing or invalid values

        if not recent_values:
            return None

        result = {
            "series_id":     series_id,
            "latest_value":  recent_values[0]["value"],
            "latest_date":   recent_values[0]["date"],
            "recent_values": recent_values,
            "source":        "FRED",
        }

        cache.set(cache_key, result, ttl=cache_ttl)
        return result

    except Exception as e:
        print(f"⚠️  FRED fetch failed for {series_id}: {e}")
        return None


async def fetch_fred_snapshot() -> dict:
    """
    Fetches all key economic indicators at once in parallel.
    This is called by Scout at the start of every pipeline run.

    Returns a dict of all available indicators.
    Failed fetches are simply omitted — never crash the pipeline.

    Example return:
    {
      "cpi_inflation": {"latest_value": 314.5, "latest_date": "2025-10"},
      "unemployment_rate": {"latest_value": 4.1, "latest_date": "2025-10"},
      "oil_price_wti": {"latest_value": 78.3, "latest_date": "2025-11-01"},
      ...
    }
    """
    cache_key = "fred:snapshot"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch all series in parallel
    tasks = {
        name: fetch_fred_series(series_id, limit=3)
        for name, series_id in KEY_SERIES.items()
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    snapshot = {}
    for name, result in zip(tasks.keys(), results):
        if isinstance(result, Exception) or result is None:
            continue  # Skip failed fetches
        snapshot[name] = result

    # Cache the full snapshot for 1 hour
    cache.set(cache_key, snapshot, ttl=3600)

    return snapshot


def format_fred_for_prompt(snapshot: dict) -> str:
    """
    Converts the FRED snapshot into a readable string
    that can be injected directly into agent prompts.

    Example output:
      FRED Economic Indicators (as of 2025-11):
        CPI Inflation:       314.5 (Oct 2025)
        Unemployment Rate:   4.1% (Oct 2025)
        Federal Funds Rate:  5.25% (Nov 2025)
        WTI Oil Price:       $78.30 (Nov 2025)
    """
    if not snapshot:
        return "FRED data unavailable"

    lines = ["FRED Economic Indicators:"]
    labels = {
        "cpi_inflation":       "CPI Inflation",
        "unemployment_rate":   "Unemployment Rate",
        "gdp_growth":          "Real GDP Growth",
        "interest_rate":       "Federal Funds Rate",
        "oil_price_wti":       "WTI Oil Price",
        "usd_eur_rate":        "USD/EUR Rate",
        "consumer_sentiment":  "Consumer Sentiment",
        "inflation_expectation":"Inflation Expectation (10yr)",
        "sp500":               "S&P 500",
        "housing_starts":      "Housing Starts",
    }

    for key, label in labels.items():
        if key in snapshot:
            val  = snapshot[key].get("latest_value", "N/A")
            date = snapshot[key].get("latest_date", "")
            lines.append(f"  {label}: {val} ({date})")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("\n🧪 Testing FRED fetcher...\n")

        # Test single series
        print("Fetching CPI data...")
        cpi = await fetch_fred_series("CPIAUCSL", limit=3)
        if cpi:
            print(f"✅ CPI: {cpi['latest_value']} ({cpi['latest_date']})")
        else:
            print("❌ CPI fetch failed")

        # Test full snapshot
        print("\nFetching full economic snapshot...")
        snapshot = await fetch_fred_snapshot()
        print(f"✅ Snapshot fetched: {len(snapshot)} indicators\n")
        print(format_fred_for_prompt(snapshot))
        print(f"\n   Cache stats: {cache.stats()}\n")

    asyncio.run(test())
