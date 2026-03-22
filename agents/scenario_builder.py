"""
agents/scenario_builder.py — Best / Base / Worst case scenario builder
========================================================================
After all domain agents and the ripple chain are complete, the Scenario
Builder creates three parallel scenarios showing what happens under
different key assumptions.

Why three scenarios matter:
  - Prevents the analysis from being falsely certain
  - Shows the range of possible outcomes
  - Helps users plan for different futures
  - Makes the uncertainty visible and explicit

Scenario types:
  Best case:  Key risks don't materialise, positive feedback loops kick in
  Base case:  Most likely path based on current evidence
  Worst case: Multiple risks compound, negative feedback loops dominate

Each scenario has:
  - Key assumptions that make this scenario play out
  - A plain-language summary of the ripple effects
  - A personalised impact (if user profile provided)
  - An estimated probability (Low / Medium / High)

Tier: tier1 (Claude Haiku) — scenario building needs structured multi-step reasoning
"""

import asyncio

from config import settings
from llm.providers import call_llm_json
from graph.state import CascadeState, ScenarioBranch


SCENARIO_SYSTEM = """You are a strategic scenario planning expert trained in futures analysis
and decision intelligence. You build rigorous, internally consistent scenarios that help
decision-makers plan for different futures. Respond with valid JSON only."""


async def run_scenario_builder(state: CascadeState) -> CascadeState:
    """
    Builds three scenario branches (best/base/worst) from the ripple chain.
    Populates state.scenarios with a list of ScenarioBranch objects.
    """
    # Build a compact ripple chain summary
    chain_summary = _summarise_ripple_chain(state)
    profile_str   = state.profile.to_prompt_string()

    prompt = f"""Build three scenarios for this event:

QUERY: {state.query}
USER PROFILE: {profile_str}

CURRENT RIPPLE CHAIN ANALYSIS:
{chain_summary}

Return JSON:
{{
  "scenarios": [
    {{
      "label":            "best_case",
      "display_name":     "Best case",
      "probability":      "Low|Medium|High",
      "key_assumptions":  ["assumption 1", "assumption 2", "assumption 3"],
      "ripple_summary":   "2-3 sentences: how this scenario plays out across the chain",
      "personal_impact":  "how this scenario specifically affects the user (or general public if no profile)"
    }},
    {{
      "label":            "base_case",
      "display_name":     "Base case",
      "probability":      "High",
      "key_assumptions":  ["assumption 1", "assumption 2", "assumption 3"],
      "ripple_summary":   "2-3 sentences: the most likely path",
      "personal_impact":  "how base case affects the user"
    }},
    {{
      "label":            "worst_case",
      "display_name":     "Worst case",
      "probability":      "Low|Medium",
      "key_assumptions":  ["assumption 1", "assumption 2", "assumption 3"],
      "ripple_summary":   "2-3 sentences: how things compound negatively",
      "personal_impact":  "how worst case affects the user"
    }}
  ]
}}"""

    try:
        data = await asyncio.wait_for(
            call_llm_json(
                prompt=prompt,
                tier="tier1",
                max_tokens=settings.MAX_TOKENS.get("scenario", 800),
                system=SCENARIO_SYSTEM,
            ),
            timeout=25,
        )

        branches = []
        for s in data.get("scenarios", []):
            branches.append(ScenarioBranch(
                label=           s.get("label", ""),
                display_name=    s.get("display_name", ""),
                key_assumptions= s.get("key_assumptions", []),
                ripple_summary=  s.get("ripple_summary", ""),
                personal_impact= s.get("personal_impact", ""),
                probability=     s.get("probability", "Medium"),
            ))

        state.scenarios = branches

        if settings.DEBUG_AGENTS:
            print(f"🎭 Scenarios: {len(branches)} branches built")

    except Exception as e:
        print(f"⚠️  Scenario builder failed: {e}")
        state.add_error("Scenario Builder", "scenarios", str(e))
        state.scenarios = []

    return state


def _summarise_ripple_chain(state: CascadeState) -> str:
    """Builds a compact text summary of the ripple chain for the prompt."""
    lines = []

    # Key agent findings (top 6 by confidence)
    sorted_outputs = sorted(
        [o for o in state.agent_outputs.values() if o.status == "complete"],
        key=lambda o: o.confidence,
        reverse=True,
    )
    for output in sorted_outputs[:6]:
        lines.append(f"• [{output.domain}] {output.finding[:200]} (confidence: {output.confidence:.0%})")

    # Ripple links
    if state.ripple_chain:
        lines.append("\nRIPPLE LINKS:")
        for link in state.ripple_chain[:5]:
            lines.append(f"  {link.from_domain} → {link.to_domain}: {link.mechanism[:150]}")

    return "\n".join(lines) or "No ripple chain data available."
