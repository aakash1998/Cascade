"""
data/fetchers/fred.py — FRED economic indicator fetcher
========================================================
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

from config import settings
from data.cache import cache


# Key economic series to fetch for every query
# Format: series_id → human-readable label
FRED_SERIES = {
    "UNRATE":      {"label": "US Unemployment Rate",     "unit": "%"},
    "CPIAUCSL":    {"label": "US CPI Inflation (YoY)",   "unit": "%"},
    "GDP":         {"label": "US Real GDP Growth",       "unit": "%"},
    "FEDFUNDS":    {"label": "Federal Funds Rate",       "unit": "%"},
    "T10Y2Y":      {"label": "Yield Curve (10Y-2Y)",     "unit": "%"},
    "DTWEXBGS":    {"label": "US Dollar Index",          "unit": ""},
    "MORTGAGE30US":{"label": "30-Year Mortgage Rate",    "unit": "%"},
    "UMCSENT":     {"label": "Consumer Sentiment",       "unit": ""},
    "ICSA":        {"label": "Initial Jobless Claims",   "unit": "K"},
    "INDPRO":      {"label": "Industrial Production",    "unit": "index"},
}

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


async def _fetch_one_series(
    client: httpx.AsyncClient,
    series_id: str,
    meta: dict,
) -> tuple[str, Optional[dict]]:
    """
    Fetches the most recent observation for one FRED series.
    Returns (series_id, data_dict) or (series_id, None) on error.
    """
    params = {
        "series_id":       series_id,
        "api_key":         settings.FRED_API_KEY or "none",  # works without key at lower limits
        "file_type":       "json",
        "sort_order":      "desc",
        "limit":           1,
        "observation_start": "2020-01-01",
    }

    try:
        resp = await client.get(FRED_BASE_URL, params=params, timeout=settings.API_TIMEOUT_SECONDS)
        resp.raise_for_status()
        observations = resp.json().get("observations", [])
        if not observations:
            return series_id, None

        obs = observations[0]
        raw_value = obs.get("value", "")

        # FRED returns "." for missing values
        if raw_value == "." or raw_value == "":
            return series_id, None

        try:
            value = round(float(raw_value), 3)
        except ValueError:
            return series_id, None

        return series_id, {
            "label": meta["label"],
            "value": value,
            "unit":  meta["unit"],
            "date":  obs.get("date", ""),
        }

    except Exception:
        return series_id, None


async def fetch_fred_indicators(series_ids: list[str] = None) -> dict:
    """
    Fetches recent values for FRED economic indicators in parallel.

    Args:
        series_ids: Optional list of specific series to fetch.
                    Defaults to FRED_SERIES (10 key indicators).

    Returns:
        Dict keyed by series_id:
          {
            "UNRATE": {"label": "US Unemployment Rate", "value": 4.1, "unit": "%", "date": "2024-12"},
            "CPIAUCSL": {...},
            ...
          }
    """
    cache_key = "fred:indicators"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    series_to_fetch = {
        k: v for k, v in FRED_SERIES.items()
        if series_ids is None or k in series_ids
    }

    results = {}

    try:
        async with httpx.AsyncClient() as client:
            tasks = [
                _fetch_one_series(client, sid, meta)
                for sid, meta in series_to_fetch.items()
            ]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        for item in raw_results:
            if isinstance(item, Exception):
                continue
            series_id, data = item
            if data is not None:
                results[series_id] = data

    except Exception as e:
        print(f"⚠️  FRED fetch error: {e}")

    cache.set(cache_key, results)
    return results
