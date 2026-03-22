"""
data/fetchers/worldbank.py — World Bank development indicator fetcher
======================================================================
The World Bank API provides 16,000+ development indicators for every
country. Completely free, no API key needed.

What we fetch:
  - GDP per capita for major economies
  - Trade openness (exports + imports as % of GDP)
  - FDI (foreign direct investment) inflows
  - Population and demographic data
  - Health and education indices

Best for: Long-run structural context, country comparisons,
          development trends. Not real-time — annual data.

API: https://api.worldbank.org/v2/

Usage:
  from data.fetchers.worldbank import fetch_worldbank_indicators
  data = await fetch_worldbank_indicators(countries=["US", "CN", "CA"])
"""

import asyncio
from typing import Optional

import httpx

from config import settings
from data.cache import cache


WB_BASE = "https://api.worldbank.org/v2"

# Key indicators with labels
WB_INDICATORS = {
    "NY.GDP.MKTP.CD":    "GDP (current USD)",
    "NY.GDP.PCAP.CD":    "GDP per capita (USD)",
    "NE.TRD.GNFS.ZS":    "Trade (% of GDP)",
    "BX.KLT.DINV.WD.GD.ZS": "FDI net inflows (% of GDP)",
    "FP.CPI.TOTL.ZG":    "Inflation (CPI, annual %)",
    "SL.UEM.TOTL.ZS":    "Unemployment rate (%)",
}

# Major economies to always fetch context for
DEFAULT_COUNTRIES = ["US", "CN", "DE", "GB", "JP", "CA", "IN", "BR"]


async def _fetch_indicator(
    client: httpx.AsyncClient,
    indicator: str,
    country_code: str,
    label: str,
) -> Optional[dict]:
    """Fetches the most recent value for one indicator + country."""
    url = f"{WB_BASE}/country/{country_code}/indicator/{indicator}"
    params = {
        "format":   "json",
        "per_page": 1,
        "mrv":      1,      # most recent value
    }

    try:
        resp = await client.get(url, params=params, timeout=settings.API_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()

        if len(data) < 2 or not data[1]:
            return None

        item = data[1][0]
        value = item.get("value")
        if value is None:
            return None

        return {
            "label":     label,
            "country":   item.get("country", {}).get("value", country_code),
            "country_code": country_code,
            "value":     round(value, 2) if isinstance(value, float) else value,
            "year":      item.get("date", ""),
            "indicator": indicator,
        }

    except Exception:
        return None


async def fetch_worldbank_indicators(
    countries: list[str] = None,
    indicators: list[str] = None,
) -> dict:
    """
    Fetches World Bank indicators for a set of countries.

    Args:
        countries:  List of ISO-2 country codes (default: major economies)
        indicators: List of WB indicator codes (default: WB_INDICATORS)

    Returns:
        Dict keyed by "{indicator}:{country}":
          {
            "NY.GDP.PCAP.CD:US": {
              "label": "GDP per capita (USD)",
              "country": "United States",
              "value": 80035.0,
              "year": "2023",
            },
            ...
          }
    """
    cache_key = "worldbank:indicators"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    countries_to_use  = countries  or DEFAULT_COUNTRIES[:4]   # limit to 4 for speed
    indicators_to_use = indicators or list(WB_INDICATORS.keys())[:4]  # 4 indicators

    results = {}
    tasks = []

    try:
        async with httpx.AsyncClient() as client:
            for ind in indicators_to_use:
                for country in countries_to_use:
                    label = WB_INDICATORS.get(ind, ind)
                    tasks.append(
                        _fetch_indicator(client, ind, country, label)
                    )

            raw = await asyncio.gather(*tasks, return_exceptions=True)

        # Reconstruct keyed results
        idx = 0
        for ind in indicators_to_use:
            for country in countries_to_use:
                item = raw[idx]
                idx += 1
                if item and not isinstance(item, Exception):
                    key = f"{ind}:{country}"
                    results[key] = item

    except Exception as e:
        print(f"⚠️  World Bank fetch error: {e}")

    cache.set(cache_key, results, ttl=86400)  # WB data: 24h cache (annual data)
    return results
