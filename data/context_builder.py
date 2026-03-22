"""
data/context_builder.py — Formats raw API data into LLM-ready context
=======================================================================
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
