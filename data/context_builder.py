"""
Takes the raw dict returned by Scout (which contains Tavily results,
FRED indicators, Finnhub quotes, GDELT events, etc.) and formats it
into a concise plain-text block that every domain agent can read.

Why this is needed:
  LLMs work best with clean, structured text — not raw JSON blobs.
  This file is the bridge between "data from APIs" and "context for agents".

What it produces:
  A string like:
    === RECENT NEWS (Tavily) ===
    - US imposes 25% tariffs on $300B of Chinese goods (Reuters, 2025-01-15)
    - China retaliates with rare earth export controls (FT, 2025-01-16)

    === ECONOMIC INDICATORS (FRED) ===
    - GDP Growth Rate: 2.3% (Q3 2024)
    - Unemployment Rate: 4.1% (Dec 2024)
    - CPI Inflation: 3.2% YoY (Dec 2024)

    === MARKET DATA (Finnhub) ===
    - S&P 500: 4,850 (+0.3%)
    - USD/CNY: 7.25 (+0.8%)

Usage:
  from data.context_builder import build_context

  context_text = build_context(state.data_context)
  # Pass context_text into every domain agent's prompt
"""

from typing import Any


def build_context(data_context: dict) -> str:
    """
    Formats the full data_context dict into a readable string for agent prompts.

    The data_context dict has this shape (keys are optional — some fetchers
    may fail and their key will be absent or empty):
      {
        "tavily":    [{"title": ..., "content": ..., "url": ..., "published_date": ...}],
        "fred":      {"GDP": {...}, "UNRATE": {...}, "CPIAUCSL": {...}},
        "finnhub":   {"quotes": {...}, "news": [...]},
        "gdelt":     [{"title": ..., "url": ..., "domain": ...}],
        "newsapi":   [{"title": ..., "description": ..., "source": ...}],
        "worldbank": {"NY.GDP.MKTP.CD": {...}, ...},
      }

    Returns a plain-text block, capped at roughly 3000 characters so it
    fits comfortably inside even the smallest model's context window.
    """
    sections = []

    # ── TAVILY — rich news search ──────────────────────────────
    if data_context.get("tavily"):
        lines = ["=== RECENT NEWS (Tavily Search) ==="]
        for item in data_context["tavily"][:6]:  # top 6 results
            title   = item.get("title", "")
            content = item.get("content", "")[:200]  # first 200 chars
            date    = item.get("published_date", "")[:10] if item.get("published_date") else ""
            url     = item.get("url", "")
            domain  = _extract_domain(url)
            date_str = f" ({date})" if date else ""
            source_str = f" [{domain}]" if domain else ""
            lines.append(f"• {title}{date_str}{source_str}")
            if content:
                lines.append(f"  {content.strip()}")
        sections.append("\n".join(lines))

    # ── NEWSAPI — additional headlines ────────────────────────
    if data_context.get("newsapi"):
        lines = ["=== NEWS HEADLINES (NewsAPI) ==="]
        for item in data_context["newsapi"][:4]:
            title  = item.get("title", "")
            source = item.get("source", {}).get("name", "") if isinstance(item.get("source"), dict) else ""
            desc   = item.get("description", "")[:150] if item.get("description") else ""
            source_str = f" [{source}]" if source else ""
            lines.append(f"• {title}{source_str}")
            if desc:
                lines.append(f"  {desc.strip()}")
        sections.append("\n".join(lines))

    # ── GDELT — global event signals ──────────────────────────
    if data_context.get("gdelt"):
        lines = ["=== GLOBAL EVENT SIGNALS (GDELT) ==="]
        for item in data_context["gdelt"][:5]:
            title  = item.get("title", "")
            domain = item.get("domain", "")
            tone   = item.get("tone", None)
            tone_str = f" [tone: {tone:.1f}]" if tone is not None else ""
            lines.append(f"• {title} [{domain}]{tone_str}")
        sections.append("\n".join(lines))

    # ── FRED — economic indicators ─────────────────────────────
    if data_context.get("fred"):
        lines = ["=== ECONOMIC INDICATORS (FRED) ==="]
        for series_id, data in data_context["fred"].items():
            if not data:
                continue
            label = data.get("label", series_id)
            value = data.get("value")
            unit  = data.get("unit", "")
            date  = data.get("date", "")[:10] if data.get("date") else ""
            if value is not None:
                date_str = f" ({date})" if date else ""
                lines.append(f"• {label}: {value}{unit}{date_str}")
        sections.append("\n".join(lines))

    # ── WORLD BANK — long-run development data ─────────────────
    if data_context.get("worldbank"):
        lines = ["=== WORLD BANK INDICATORS ==="]
        for indicator, data in data_context["worldbank"].items():
            if not data:
                continue
            label   = data.get("label", indicator)
            country = data.get("country", "")
            value   = data.get("value")
            year    = data.get("year", "")
            if value is not None:
                country_str = f" ({country})" if country else ""
                lines.append(f"• {label}{country_str}: {value} [{year}]")
        sections.append("\n".join(lines))

    # ── FINNHUB — market prices + company news ─────────────────
    if data_context.get("finnhub"):
        fh = data_context["finnhub"]

        # Market quotes
        if fh.get("quotes"):
            lines = ["=== MARKET DATA (Finnhub) ==="]
            for symbol, quote in fh["quotes"].items():
                price  = quote.get("c", "N/A")    # current price
                change = quote.get("dp", "N/A")   # % change
                lines.append(f"• {symbol}: {price} ({change:+.2f}%)" if isinstance(change, (int, float)) else f"• {symbol}: {price}")
            sections.append("\n".join(lines))

        # Company/sector news
        if fh.get("news"):
            lines = ["=== MARKET NEWS (Finnhub) ==="]
            for item in fh["news"][:4]:
                headline = item.get("headline", "")
                source   = item.get("source", "")
                lines.append(f"• {headline} [{source}]")
            sections.append("\n".join(lines))

    # ── FALLBACK — nothing fetched ─────────────────────────────
    if not sections:
        return (
            "=== DATA CONTEXT ===\n"
            "No external data was fetched for this query.\n"
            "Base analysis on general knowledge only."
        )

    full_text = "\n\n".join(sections)

    # Hard cap at 4000 chars to stay within token limits
    if len(full_text) > 4000:
        full_text = full_text[:3970] + "\n... [context truncated]"

    return full_text


def build_agent_prompt(
    query: str,
    domain: str,
    focus: str,
    data_context: dict,
    profile_string: str = "",
    conversation_history: list = None,
) -> str:
    """
    Builds the full prompt for one domain agent.

    Combines:
      - The original user query
      - The agent's specific focus area
      - The formatted data context
      - The user's profile (if provided)
      - Relevant conversation history

    Returns a ready-to-send prompt string.
    """
    context_text = build_context(data_context)

    # History (last 2 turns only — keep it short)
    history_text = ""
    if conversation_history:
        recent = conversation_history[-4:]  # last 2 user+assistant pairs
        history_lines = []
        for turn in recent:
            role = "User" if turn.get("role") == "user" else "Assistant"
            content = turn.get("content", "")[:300]
            history_lines.append(f"{role}: {content}")
        if history_lines:
            history_text = "\n=== CONVERSATION CONTEXT ===\n" + "\n".join(history_lines)

    # User profile
    profile_text = ""
    if profile_string and profile_string != "No profile provided":
        profile_text = f"\n=== USER PROFILE ===\n{profile_string}"

    prompt = f"""You are analyzing the ripple effects of a world event from the {domain.upper()} domain perspective.

ORIGINAL QUERY: {query}

YOUR SPECIFIC FOCUS: {focus}
{history_text}{profile_text}

=== REAL-TIME DATA ===
{context_text}

=== YOUR TASK ===
Analyze how this event specifically affects the {domain} domain.
Focus on: {focus}

Return ONLY a JSON object with these exact keys:
{{
  "finding": "Your detailed analysis (2-4 sentences with specific data points)",
  "confidence": 0.0-1.0 (how confident you are based on available evidence),
  "sources": ["list", "of", "data", "sources", "you", "used"],
  "data_points": ["specific", "numbers", "or", "facts", "from", "the", "data"],
  "downstream_signals": ["domains", "affected", "next", "e.g.", "Labour", "Inflation"],
  "timeframe": "when this impact hits (e.g. '1-3 months', '6-12 months')",
  "severity": "low|medium|high|critical",
  "uncertainty_note": "key uncertainty or caveat (1 sentence)",
  "contradicting_view": "strongest argument against your finding (1 sentence)"
}}"""

    return prompt


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Extracts the domain name from a URL for display."""
    if not url:
        return ""
    try:
        # Simple extraction without importing urllib
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        return url.split("/")[0].split("?")[0]
    except Exception:
        return ""


# ─────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🧪 Testing context_builder...\n")

    sample_context = {
        "tavily": [
            {
                "title": "US imposes 25% tariffs on Chinese goods",
                "content": "The Biden administration has imposed sweeping tariffs affecting $300 billion in Chinese imports across technology, steel, and consumer goods sectors.",
                "url": "https://www.reuters.com/article/trade-war",
                "published_date": "2025-01-15T10:00:00Z",
            }
        ],
        "fred": {
            "GDP": {"label": "US GDP Growth Rate", "value": "2.3%", "unit": "", "date": "2024-09-30"},
            "UNRATE": {"label": "Unemployment Rate", "value": 4.1, "unit": "%", "date": "2024-12-01"},
        },
        "finnhub": {
            "quotes": {"SPY": {"c": 485.20, "dp": 0.34}},
            "news": [{"headline": "Markets react to trade tensions", "source": "Bloomberg"}],
        },
    }

    result = build_context(sample_context)
    print("Context output:")
    print(result)
    print(f"\nLength: {len(result)} chars")

    assert "Tavily" in result
    assert "FRED" in result
    assert "Finnhub" in result
    print("\n✅ context_builder tests passed\n")
data/context_builder.py — Data Context Builder
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
