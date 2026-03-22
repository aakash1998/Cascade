"""
agents/scout.py — Scout Agent (Data Fetcher)
=============================================
Scout is the data layer agent. It runs before any domain agent
and fetches live data from all sources in parallel.

Why Scout exists:
  Without Scout, every domain agent would make its own API calls.
  That means 20 agents × 3 APIs each = 60 API calls per query.
  With Scout, all data is fetched ONCE and shared with every agent
  via state.data_context — 6 API calls total.

What Scout fetches (all in parallel):
  1. Tavily    — general web search + per-domain searches
  2. FRED      — US economic indicators (CPI, unemployment, rates)
  3. Finnhub   — financial market news
  4. World Bank — global economic data for 10 major economies
  5. NewsAPI   — current headlines (if key available)
  6. GDELT     — world events and sentiment (if available)

What Scout writes to state:
  state.data_context     — the full data dict for all agents
  state.data_sources_used — which sources responded
  state.data_fetched_at  — timestamp

Scout has NO LLM calls — it is pure data fetching code.
This makes it fast, cheap, and deterministic.

Usage:
  from agents.scout import run_scout
  state = await run_scout(state)
  print(state.data_context["fred"]["unemployment_rate"])
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timezone

from config import settings
from graph.state import CascadeState
from data.context_builder import build_data_context, summarise_context
from data.fetchers.gdelt     import fetch_gdelt_events
from data.fetchers.worldbank import fetch_worldbank_snapshot
from data.fetchers.newsapi   import fetch_newsapi_snapshot


async def run_scout(state: CascadeState) -> CascadeState:
    """
    Runs the Scout agent — fetches all data before domain agents start.

    Reads:  state.query, state.manifest (for domain list)
    Writes: state.data_context, state.data_sources_used,
            state.data_fetched_at

    Args:
        state: Current pipeline state

    Returns:
        Updated state with data_context populated

    This is called as the second node in the LangGraph pipeline,
    right after the Orchestrator returns the manifest.
    """
    state.current_phase = "fetching"

    # Get the list of domains from the manifest
    # So we only fetch domain-specific data for agents actually running
    domains = [
        agent["domain"] if "domain" in agent
        else agent["name"].replace(" Agent", "").lower().replace(" ", "_")
        for agent in state.manifest.agents
    ]

    if settings.DEBUG_AGENTS:
        print(f"\n🔍 Scout fetching data for domains: {domains}")

    try:
        # ── Core fetches via context_builder ──────────────────────
        # Tavily + FRED + Finnhub run via context_builder in parallel
        core_context = await build_data_context(
            query=state.query,
            domains=domains,
        )

        # ── Additional fetches in parallel ────────────────────────
        # World Bank, NewsAPI, GDELT run alongside core fetches

        additional_tasks = {
            "worldbank": fetch_worldbank_snapshot(),
            "newsapi":   fetch_newsapi_snapshot(state.query),
            "gdelt":     fetch_gdelt_events(state.query, max_items=5),
        }

        additional_results = await asyncio.gather(
            *additional_tasks.values(),
            return_exceptions=True,
        )

        additional = {}
        for key, result in zip(additional_tasks.keys(), additional_results):
            if not isinstance(result, Exception) and result:
                additional[key] = result
                if settings.DEBUG_AGENTS:
                    print(f"   ✅ {key} data fetched")
            else:
                if settings.DEBUG_AGENTS:
                    print(f"   ⚠️  {key} unavailable — continuing without it")

        # ── Merge everything into one context dict ─────────────────
        full_context = {**core_context, **additional}

        # ── Write to state ─────────────────────────────────────────
        state.data_context      = full_context
        state.data_sources_used = full_context.get("sources_used", [])
        state.data_fetched_at   = datetime.now(timezone.utc).isoformat()

        # Add any extra sources from additional fetches
        for key in additional.keys():
            source = key.capitalize()
            if source not in state.data_sources_used:
                state.data_sources_used.append(source)

        state.mark_phase_complete("fetching")

        if settings.DEBUG_AGENTS:
            print(f"\n   {summarise_context(full_context)}")
            print(f"   Sources: {state.data_sources_used}")

        print(f"✅ Scout: data fetched from {len(state.data_sources_used)} sources")

    except Exception as e:
        # Scout failure is non-fatal — agents can still run on LLM knowledge
        error_msg = f"Scout fetch failed: {str(e)}"
        state.add_error("Scout", "fetching", error_msg)
        print(f"⚠️  {error_msg} — agents will run without live data")

        # Set empty context so agents don't crash on missing key
        state.data_context      = {}
        state.data_sources_used = []
        state.data_fetched_at   = datetime.now(timezone.utc).isoformat()

    return state


# ─────────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test Scout with a real query:
      python -m agents.scout
    """
    import asyncio
    from graph.state import create_initial_state
    from agents.orchestrator import run_orchestrator

    async def test():
        print("\n🧪 Testing Scout Agent...\n")

        # First run orchestrator to get the manifest
        state = create_initial_state(
            query="What does rising US inflation mean for housing and jobs?",
            session_id="test-scout-001",
            profile={"job": "Teacher", "city": "Calgary, Canada"},
        )

        print("Step 1: Running Orchestrator to get manifest...")
        state = await run_orchestrator(state)
        print(f"   Manifest: {len(state.manifest.agents)} agents selected")

        print("\nStep 2: Running Scout to fetch data...")
        import time
        start = time.time()
        state = await run_scout(state)
        elapsed = time.time() - start

        print(f"\n✅ Scout complete in {elapsed:.1f}s")
        print(f"   Sources used:    {state.data_sources_used}")
        print(f"   Context keys:    {[k for k in state.data_context.keys() if not k.endswith('_formatted')]}")
        print(f"   Fetched at:      {state.data_fetched_at}")
        print(f"   Errors:          {len(state.errors)}")

        # Show a sample of what was fetched
        fred = state.data_context.get("fred", {})
        if fred:
            unemp = fred.get("unemployment_rate", {})
            if unemp:
                print(f"\n   Live unemployment: {unemp.get('latest_value')}% ({unemp.get('latest_date')})")

        tavily = state.data_context.get("tavily_general", [])
        if tavily:
            print(f"   Top Tavily result: {tavily[0]['title'][:60]}")

        worldbank = state.data_context.get("worldbank", {})
        if worldbank:
            us = worldbank.get("US", {})
            if us:
                print(f"   US GDP (World Bank): ${us.get('gdp_usd', 0)/1e12:.1f}T")

        print("\n✅ Scout test complete\n")

    asyncio.run(test())