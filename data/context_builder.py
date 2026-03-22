"""
data/context_builder.py — Data Context Builder
================================================
This is the Scout agent's engine. It fetches data from all
sources in parallel and assembles everything into one clean
context object that gets passed to every domain agent.

Why parallel fetching matters:
  If we fetched sources one by one:
    Tavily (2s) + FRED (1s) + Finnhub (1s) = 4 seconds minimum
  Fetching all in parallel:
    max(Tavily, FRED, Finnhub) = ~2 seconds total

  At 20+ agents per query, this saving compounds quickly.

What agents receive:
  Every domain agent gets the same data context object.
  The base_agent._extract_relevant_data() method then filters
  it down to only the sections relevant to that specific domain.

Usage:
  from data.context_builder import build_data_context

  context = await build_data_context(
      query="What does rising inflation mean for housing?",
      domains=["inflation", "housing", "finance"]
  )
  # context is a dict passed to all agents via state.data_context
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timezone
from config import settings
from data.fetchers.tavily  import fetch_tavily_for_domain, fetch_tavily
from data.fetchers.fred    import fetch_fred_snapshot, format_fred_for_prompt
from data.fetchers.finnhub import fetch_finnhub_snapshot, format_finnhub_for_prompt


async def build_data_context(
    query:   str,
    domains: list[str] = None,
) -> dict:
    """
    Fetches all data sources in parallel and returns a unified
    context dict that agents use to ground their analysis.

    Args:
        query:   The user's original query
        domains: List of domain names that need data
                 (from the orchestrator manifest)
                 If None, fetches all general sources.

    Returns:
        A dict with keys for each data source:
        {
          "tavily_general":  [...],     # General search results
          "tavily_energy":   [...],     # Energy-specific results
          "tavily_labour":   [...],     # Labour-specific results
          ...
          "fred":            {...},     # Economic indicators
          "fred_formatted":  "...",     # Human-readable FRED string
          "finnhub":         {...},     # Market data
          "finnhub_formatted":"...",    # Human-readable Finnhub string
          "fetched_at":      "...",     # Timestamp
          "sources_used":    [...],     # Which sources responded
        }
    """
    context = {}
    sources_used = []
    domains = domains or []

    # ── Build all fetch tasks in parallel ─────────────────────────

    tasks = {}

    # 1. General Tavily search — always run
    tasks["tavily_general"] = fetch_tavily(query, max_results=5)

    # 2. Domain-specific Tavily searches
    # Only fetch for domains the orchestrator selected
    for domain in domains:
        tasks[f"tavily_{domain}"] = fetch_tavily_for_domain(domain, query)

    # 3. FRED economic snapshot — always run (free, no key needed)
    tasks["fred"] = fetch_fred_snapshot()

    # 4. Finnhub market data — always run if key available
    if settings.FINNHUB_API_KEY:
        tasks["finnhub"] = fetch_finnhub_snapshot()

    # ── Run all tasks in parallel ──────────────────────────────────

    keys    = list(tasks.keys())
    results = await asyncio.gather(
        *tasks.values(),
        return_exceptions=True,   # Never crash — exceptions return as values
    )

    # ── Assemble context ──────────────────────────────────────────

    for key, result in zip(keys, results):
        if isinstance(result, Exception):
            # Log but don't crash — missing data just lowers confidence
            print(f"⚠️  Data fetch failed for {key}: {result}")
            continue

        if result:
            context[key] = result
            # Track which sources responded
            source_name = key.split("_")[0].capitalize()
            if source_name not in sources_used:
                sources_used.append(source_name)

    # ── Add formatted versions for easy prompt injection ──────────

    if "fred" in context:
        context["fred_formatted"] = format_fred_for_prompt(context["fred"])

    if "finnhub" in context:
        context["finnhub_formatted"] = format_finnhub_for_prompt(context["finnhub"])

    # ── Metadata ──────────────────────────────────────────────────

    context["fetched_at"]   = datetime.now(timezone.utc).isoformat()
    context["sources_used"] = sources_used
    context["query"]        = query

    return context


def summarise_context(context: dict) -> str:
    """
    Returns a one-line summary of what data was fetched.
    Used in the UI status messages and debug logging.

    Example: "Fetched from: Tavily (8 results), FRED (9 indicators), Finnhub (forex)"
    """
    parts = []

    # Count Tavily results
    tavily_count = 0
    for key, val in context.items():
        if key.startswith("tavily") and isinstance(val, list):
            tavily_count += len(val)
    if tavily_count > 0:
        parts.append(f"Tavily ({tavily_count} results)")

    # Count FRED indicators
    fred = context.get("fred", {})
    if fred:
        parts.append(f"FRED ({len(fred)} indicators)")

    # Finnhub
    finnhub = context.get("finnhub", {})
    if finnhub.get("forex"):
        parts.append(f"Finnhub (forex + news)")

    if not parts:
        return "No external data fetched"

    return "Fetched from: " + ", ".join(parts)


# ─────────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("\n🧪 Testing Context Builder...\n")

        query   = "What does the US-China trade war mean for energy and labour markets?"
        domains = ["trade", "energy", "labour", "inflation"]

        print(f"Query: {query[:60]}...")
        print(f"Domains: {domains}")
        print("\nFetching all data sources in parallel...")

        import time
        start = time.time()
        context = await build_data_context(query, domains)
        elapsed = time.time() - start

        print(f"\n✅ Context built in {elapsed:.1f}s")
        print(f"   {summarise_context(context)}")
        print(f"   Sources used: {context.get('sources_used', [])}")
        print(f"   Context keys: {[k for k in context.keys() if not k.endswith('_formatted')]}")

        # Show FRED data
        if "fred_formatted" in context:
            print(f"\n{context['fred_formatted']}")

        # Show Finnhub data
        if "finnhub_formatted" in context:
            print(f"\n{context['finnhub_formatted']}")

        # Show Tavily results count
        tavily_general = context.get("tavily_general", [])
        if tavily_general:
            print(f"\nTavily general results: {len(tavily_general)}")
            print(f"  Top result: {tavily_general[0]['title'][:60]}")

        print("\n✅ Context builder test complete\n")

    asyncio.run(test())