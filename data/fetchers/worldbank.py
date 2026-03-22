"""
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

data/fetchers/worldbank.py — World Bank Data Fetcher
The World Bank provides free economic and development data
for 196 countries. No API key needed.

Why this is valuable for Cascade:
  FRED is mostly US-focused. World Bank fills the gap for
  global coverage — especially developing countries that
  matter a lot when analysing conflicts, migration, food
  security, and geopolitical events.

Key indicators we fetch:
  NY.GDP.MKTP.CD  — GDP (current USD)
  FP.CPI.TOTL.ZG  — Inflation rate
  SL.UEM.TOTL.ZS  — Unemployment rate
  SP.POP.TOTL     — Total population
  SI.POV.DDAY     — Poverty headcount ratio
  NE.TRD.GNFS.ZS  — Trade as % of GDP

Usage:
  from data.fetchers.worldbank import fetch_country_indicators

  data = await fetch_country_indicators(["US", "CN", "DE"])
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import httpx
from config import settings
from data.cache import cache


WORLDBANK_BASE = "https://api.worldbank.org/v2"

# Key indicators — { friendly_name: world_bank_indicator_code }
KEY_INDICATORS = {
    "gdp_usd":        "NY.GDP.MKTP.CD",
    "inflation_rate": "FP.CPI.TOTL.ZG",
    "unemployment":   "SL.UEM.TOTL.ZS",
    "population":     "SP.POP.TOTL",
    "trade_pct_gdp":  "NE.TRD.GNFS.ZS",
    "poverty_rate":   "SI.POV.DDAY",
}

# Country codes for major economies — used in snapshot
MAJOR_ECONOMIES = ["US", "CN", "DE", "JP", "GB", "IN", "BR", "CA", "FR", "RU"]


async def fetch_country_indicators(
    country_codes: list[str],
    indicators:    list[str] = None,
    cache_ttl:     int = 7200,   # 2 hours — World Bank data changes slowly
) -> dict:
    """
    Fetches economic indicators for a list of countries.

    Args:
        country_codes: ISO 2-letter country codes ["US", "CN", "DE"]
        indicators:    List of indicator names to fetch
                       (uses KEY_INDICATORS keys, e.g. ["gdp_usd", "inflation_rate"])
                       If None, fetches all key indicators.
        cache_ttl:     Cache duration in seconds

    Returns:
        Nested dict: { "US": { "gdp_usd": 25e12, "inflation_rate": 3.2 }, ... }
    """
    if not country_codes:
        return {}

    indicators = indicators or list(KEY_INDICATORS.keys())
    cache_key  = f"worldbank:{'_'.join(sorted(country_codes))}:{'_'.join(indicators)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = {code: {} for code in country_codes}
    country_str = ";".join(country_codes)

    async def fetch_indicator(friendly_name: str, wb_code: str):
        """Fetches one indicator for all requested countries."""
        try:
            url = f"{WORLDBANK_BASE}/country/{country_str}/indicator/{wb_code}"
            params = {
                "format":   "json",
                "mrv":      1,       # most recent value only
                "per_page": 50,
            }

            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            # World Bank returns [metadata, data_array]
            if len(data) < 2 or not data[1]:
                return

            for entry in data[1]:
                country_code = entry.get("countryiso3code", "")[:2]
                value        = entry.get("value")
                if country_code in result and value is not None:
                    result[country_code][friendly_name] = round(float(value), 2)

        except Exception as e:
            print(f"⚠️  World Bank fetch failed ({wb_code}): {e}")

    # Fetch all indicators in parallel
    tasks = [
        fetch_indicator(name, code)
        for name, code in KEY_INDICATORS.items()
        if name in indicators
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    cache.set(cache_key, result, ttl=cache_ttl)
    return result


async def fetch_worldbank_snapshot() -> dict:
    """
    Fetches key indicators for all major economies.
    Called by Scout for every pipeline run.

    Returns data for US, China, Germany, Japan, UK, India,
    Brazil, Canada, France, Russia.
    """
    cache_key = "worldbank:snapshot"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = await fetch_country_indicators(
        country_codes=MAJOR_ECONOMIES,
        indicators=["gdp_usd", "inflation_rate", "unemployment", "trade_pct_gdp"],
    )

    cache.set(cache_key, data, ttl=7200)
    return data


def format_worldbank_for_prompt(data: dict) -> str:
    """
    Converts World Bank data into readable string for agent prompts.

    Example output:
      World Bank Indicators (latest available):
        US:  GDP $25.5T | Inflation 3.2% | Unemployment 3.7%
        CN:  GDP $17.9T | Inflation 0.4% | Unemployment 5.1%
    """
    if not data:
        return "World Bank data unavailable"

    lines = ["World Bank Indicators (latest available):"]

    country_names = {
        "US": "United States", "CN": "China", "DE": "Germany",
        "JP": "Japan", "GB": "United Kingdom", "IN": "India",
        "BR": "Brazil", "CA": "Canada", "FR": "France", "RU": "Russia",
    }

    for code, indicators in data.items():
        if not indicators:
            continue
        name = country_names.get(code, code)
        parts = []
        if "gdp_usd" in indicators:
            gdp_t = indicators["gdp_usd"] / 1e12
            parts.append(f"GDP ${gdp_t:.1f}T")
        if "inflation_rate" in indicators:
            parts.append(f"Inflation {indicators['inflation_rate']}%")
        if "unemployment" in indicators:
            parts.append(f"Unemployment {indicators['unemployment']}%")
        if parts:
            lines.append(f"  {name}: {' | '.join(parts)}")

    return "\n".join(lines)


if __name__ == "__main__":
    async def test():
        print("\n🧪 Testing World Bank fetcher...\n")

        print("Fetching snapshot for major economies...")
        data = await fetch_worldbank_snapshot()

        if data:
            print(f"✅ World Bank data fetched for {len(data)} countries\n")
            print(format_worldbank_for_prompt(data))
        else:
            print("⚠️  No World Bank data returned")

        print()

    asyncio.run(test())
