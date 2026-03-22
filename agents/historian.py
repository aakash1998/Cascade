"""
agents/historian.py — Historical pattern matching agent
=========================================================
The Historian searches for events in the past that are structurally
similar to the current query. Historical parallels help calibrate
predictions: if we've seen this before, we know the playbook.

Examples:
  Query: "US imposes 25% tariffs on China"
  Parallels: Smoot-Hawley Act 1930, US-Japan trade war 1980s,
             2018-2020 US-China trade war Round 1

The Historian extracts:
  - What happened last time (the parallel event)
  - What the key outcome was
  - How long it took to play out
  - What was different that time vs now
  - The confidence that this parallel applies

This gives the final summary historical grounding and makes
predictions more credible ("the last time this happened...").

Tier: tier2 (Groq) — historical knowledge is well within Llama 70B capability
"""

import asyncio

from config import settings
from llm.providers import call_llm_json
from graph.state import CascadeState


HISTORIAN_SYSTEM = """You are a world history and economic history expert with deep knowledge
of past geopolitical crises, financial crashes, trade wars, commodity shocks, and policy changes.
You identify historical parallels to current events with precision and nuance.
Respond with valid JSON only."""


async def run_historian(state: CascadeState) -> CascadeState:
    """
    Finds historical parallels for the current query.
    Populates state.historical_parallels.
    """
    prompt = f"""Identify 2-3 historical events that are most similar to this current event:

CURRENT EVENT: {state.query}

KEY DOMAINS AFFECTED: {", ".join(
    state.agent_outputs[n].domain
    for n in state.get_completed_agents()[:6]
)}

Return JSON:
{{
  "parallels": [
    {{
      "event":       "Name of the historical event",
      "year":        "Year or period (e.g. '1973', '2008-2009', '1985-1990')",
      "summary":     "What happened and why it's similar (2-3 sentences)",
      "outcome":     "What the key outcome was",
      "timeframe":   "How long the main effects lasted",
      "differences": "Key ways today's situation differs (1-2 sentences)",
      "lesson":      "The main lesson or precedent this sets",
      "similarity_score": 0.0-1.0
    }}
  ],
  "historical_context": "1-2 sentences placing today's event in historical perspective"
}}"""

    try:
        data = await asyncio.wait_for(
            call_llm_json(
                prompt=prompt,
                tier="tier2",
                max_tokens=settings.MAX_TOKENS.get("historian", 600),
                system=HISTORIAN_SYSTEM,
            ),
            timeout=20,
        )

        state.historical_parallels = data.get("parallels", [])

        if settings.DEBUG_AGENTS:
            print(f"📚 Historian: {len(state.historical_parallels)} parallels found")

    except Exception as e:
        print(f"⚠️  Historian failed: {e}")
        state.add_error("Historian", "historical", str(e))
        state.historical_parallels = []

    return state
