"""
agents/debate_moderator.py — Finds and resolves conflicting agent views
========================================================================
After all domain agents complete, the Debate Moderator:

  1. Identifies pairs of agents with contradicting findings
     (e.g. Finance Agent says "rates will fall", Inflation Agent says "rates must rise")

  2. Calls the LLM to adjudicate the conflict with explicit reasoning

  3. Stores the conflicts and resolution in state so they can be shown
     in the UI as a "debate" section

This is the feature that separates Cascade from a simple summariser —
it surfaces real uncertainty and shows how experts disagree.

Tier: tier1 (Claude Haiku) — needs nuanced reasoning to adjudicate debates
      Falls back to Groq if Claude unavailable
"""

import asyncio

from config import settings
from llm.providers import call_llm_json
from graph.state import CascadeState


DEBATE_SYSTEM = """You are a highly experienced economic policy advisor and debate moderator.
You adjudicate disagreements between specialist analysts, weighing evidence carefully.
You do not pick sides without reason — you explain why one view is better supported by data.
Respond with valid JSON only."""


async def run_debate_moderator(state: CascadeState) -> CascadeState:
    """
    Identifies conflicts between domain agents and adjudicates them.
    Skipped if fewer than 3 agents completed (not enough to find conflicts).
    """
    completed = state.get_completed_agents()
    if len(completed) < 3:
        state.debate_conflicts  = []
        state.debate_resolution = "Insufficient agents for debate round."
        return state

    if settings.DEBUG_AGENTS:
        print(f"🥊 Debate moderator reviewing {len(completed)} agents...")

    # Build a compact summary of all findings
    findings_summary = "\n".join(
        f"[{name}] confidence={state.agent_outputs[name].confidence:.2f}: "
        f"{state.agent_outputs[name].finding[:250]} "
        f"| downstream: {', '.join(state.agent_outputs[name].downstream_signals[:3])}"
        for name in completed[:12]
    )

    prompt = f"""Review these analyst findings and identify any significant contradictions:

QUERY: {state.query}

ANALYST FINDINGS:
{findings_summary}

Return JSON with this structure:
{{
  "conflicts": [
    {{
      "agents":      ["Agent A Name", "Agent B Name"],
      "topic":       "What they disagree about",
      "agent_a_view": "Agent A's position",
      "agent_b_view": "Agent B's position",
      "resolution":  "Which view is better supported and why",
      "confidence_in_resolution": 0.0-1.0
    }}
  ],
  "overall_resolution": "1-2 sentences summarising how conflicting views are resolved in the big picture",
  "consensus_strength": "strong|moderate|weak"
}}

If there are no meaningful conflicts, return: {{"conflicts": [], "overall_resolution": "Analysts broadly agree on the direction of impacts.", "consensus_strength": "strong"}}"""

    try:
        data = await asyncio.wait_for(
            call_llm_json(
                prompt=prompt,
                tier="tier1",
                max_tokens=settings.MAX_TOKENS.get("debate", 400),
                system=DEBATE_SYSTEM,
            ),
            timeout=25,
        )

        state.debate_conflicts  = data.get("conflicts", [])
        state.debate_resolution = data.get("overall_resolution", "")

        if settings.DEBUG_AGENTS:
            print(f"🥊 Debate: {len(state.debate_conflicts)} conflicts found")

    except Exception as e:
        print(f"⚠️  Debate moderator failed: {e}")
        state.add_error("Debate Moderator", "debate", str(e))
        state.debate_conflicts  = []
        state.debate_resolution = "Debate round unavailable."

    return state
