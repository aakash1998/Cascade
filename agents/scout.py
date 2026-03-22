"""
agents/scout.py — Parallel data fetcher / context assembler
============================================================
Scout runs immediately after the Orchestrator. Its job is to gather
real-time data from all available APIs in parallel before the domain
agents start. This way, every domain agent gets fresh data without
each making its own API calls.

What Scout fetches (all in parallel):
  1. Tavily   — rich web search for current news
  2. FRED     — US economic indicators (GDP, inflation, unemployment)
  3. Finnhub  — market data (stock indices, commodities)
  4. GDELT    — global event signals + sentiment scores
  5. NewsAPI  — additional news headlines (if key available)
  6. WorldBank — long-run development indicators

Results are merged into state.data_context, a dict that every
domain agent reads when building its prompt.

Why parallel fetching matters:
  If Scout called APIs sequentially, 6 sources × 5s each = 30s wait.
  In parallel, all 6 complete in ~5-8s (limited by the slowest source).
"""

import asyncio

from config import settings
from graph.state import CascadeState
from data.fetchers.tavily    import fetch_tavily
from data.fetchers.fred      import fetch_fred_indicators
from data.fetchers.finnhub   import fetch_finnhub_data
from data.fetchers.gdelt     import fetch_gdelt_events
from data.fetchers.newsapi   import fetch_newsapi_headlines
from data.fetchers.worldbank import fetch_worldbank_indicators


async def run_scout(state: CascadeState) -> CascadeState:
    """
    Fetches data from all sources in parallel and populates state.data_context.
    Called as the second pipeline node (after Orchestrator).

    The data_context dict format:
      {
        "tavily":    [article dicts...],
        "fred":      {series_id: {label, value, unit, date}},
        "finnhub":   {quotes: {...}, news: [...]},
        "gdelt":     [event dicts...],
        "newsapi":   [article dicts...],
        "worldbank": {indicator_country_key: {label, value, ...}},
      }
    """
    query = state.query

    if settings.DEBUG_AGENTS:
        print(f"🔭 Scout fetching data for: {query[:60]}...")

    # ── All API calls fire simultaneously ─────────────────────
    (
        tavily_results,
        fred_results,
        finnhub_results,
        gdelt_results,
        newsapi_results,
        worldbank_results,
    ) = await asyncio.gather(
        _safe_fetch("tavily",    fetch_tavily(query)),
        _safe_fetch("fred",      fetch_fred_indicators()),
        _safe_fetch("finnhub",   fetch_finnhub_data(query)),
        _safe_fetch("gdelt",     fetch_gdelt_events(query)),
        _safe_fetch("newsapi",   fetch_newsapi_headlines(query)),
        _safe_fetch("worldbank", fetch_worldbank_indicators()),
    )

    # ── Assemble the data context dict ─────────────────────────
    data_context: dict = {}
    sources_used: list = []

    if tavily_results:
        data_context["tavily"] = tavily_results
        sources_used.append("Tavily")

    if fred_results:
        data_context["fred"] = fred_results
        sources_used.append("FRED")

    if finnhub_results and (finnhub_results.get("quotes") or finnhub_results.get("news")):
        data_context["finnhub"] = finnhub_results
        sources_used.append("Finnhub")

    if gdelt_results:
        data_context["gdelt"] = gdelt_results
        sources_used.append("GDELT")

    if newsapi_results:
        data_context["newsapi"] = newsapi_results
        sources_used.append("NewsAPI")

    if worldbank_results:
        data_context["worldbank"] = worldbank_results
        sources_used.append("World Bank")

    from datetime import datetime, timezone
    state.data_context      = data_context
    state.data_sources_used = sources_used
    state.data_fetched_at   = datetime.now(timezone.utc).isoformat()
    state.mark_phase_complete("fetching")

    if settings.DEBUG_AGENTS:
        print(f"✅ Scout done — sources: {', '.join(sources_used) or 'none'}")

    return state


async def _safe_fetch(name: str, coro) -> any:
    """
    Wraps a fetcher coroutine with a timeout and error catch.
    Returns the result, or an empty dict/list on failure.
    This ensures one failing source doesn't block all others.
    """
    try:
        result = await asyncio.wait_for(coro, timeout=settings.API_TIMEOUT_SECONDS + 5)
        return result
    except asyncio.TimeoutError:
        print(f"⏱️  Scout: {name} timed out")
        return {} if name in ("fred", "finnhub", "worldbank") else []
    except Exception as e:
        print(f"⚠️  Scout: {name} failed — {e}")
        return {} if name in ("fred", "finnhub", "worldbank") else []
