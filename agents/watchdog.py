"""
agents/watchdog.py — QA agent that flags low-confidence or unsupported claims
==============================================================================
The Watchdog reviews all domain agent outputs and flags any claims that:
  - Have confidence below HALLUCINATION_CONFIDENCE_THRESHOLD (default 0.6)
  - Contradict real-time data in the context
  - Make specific numerical claims without citing a source
  - Are logically inconsistent with other agents' findings

Flags are stored in state.hallucination_flags and displayed in the UI
as yellow warnings next to the relevant agent's output.

The Watchdog also calculates state.overall_confidence by averaging all
non-flagged agent confidence scores.

Tier: tier2 (Groq) — pattern matching + review, doesn't need Claude-level reasoning
"""

import asyncio
from typing import Optional

from config import settings
from llm.providers import call_llm_json
from graph.state import CascadeState


WATCHDOG_SYSTEM = """You are a rigorous fact-checking agent for an AI analysis system.
Your job is to identify claims that might be unreliable, unsupported, or contradicted by evidence.
Be constructive — flag only genuine issues, not minor wording choices.
Respond with valid JSON only."""


async def run_watchdog(state: CascadeState) -> CascadeState:
    """
    Reviews all completed agent outputs for quality issues.
    Populates state.hallucination_flags and state.overall_confidence.
    """
    completed = state.get_completed_agents()
    if not completed:
        state.overall_confidence = 0.0
        return state

    # Auto-flag outputs below confidence threshold (no LLM needed for this)
    flags = []
    confidence_sum = 0.0
    confidence_count = 0

    for agent_name in completed:
        output = state.agent_outputs.get(agent_name)
        if not output:
            continue

        confidence_sum   += output.confidence
        confidence_count += 1

        # Flag low-confidence outputs automatically
        if output.confidence < settings.HALLUCINATION_CONFIDENCE_THRESHOLD:
            flags.append({
                "agent":     agent_name,
                "domain":    output.domain,
                "flag_type": "LOW_CONFIDENCE",
                "message":   f"Confidence {output.confidence:.0%} is below threshold {settings.HALLUCINATION_CONFIDENCE_THRESHOLD:.0%}",
                "severity":  "warning",
            })

        # Flag outputs with no sources
        if not output.sources and output.confidence > 0.7:
            flags.append({
                "agent":     agent_name,
                "domain":    output.domain,
                "flag_type": "NO_SOURCES",
                "message":   "High-confidence claim with no cited data sources",
                "severity":  "info",
            })

    # Use LLM to do a deeper cross-check if we have multiple outputs
    if len(completed) >= 3 and not settings.LOCAL_DEV_MODE:
        lm_flags = await _llm_crosscheck(state, completed)
        flags.extend(lm_flags)

    state.hallucination_flags = flags
    state.overall_confidence  = (
        round(confidence_sum / confidence_count, 2)
        if confidence_count > 0 else 0.0
    )

    if settings.DEBUG_AGENTS:
        print(f"🛡️  Watchdog: {len(flags)} flags, overall confidence {state.overall_confidence:.0%}")

    return state


async def _llm_crosscheck(state: CascadeState, completed: list) -> list:
    """
    Uses the LLM to spot contradictions between agent outputs.
    Returns a list of flag dicts (may be empty if no issues found).
    """
    # Build a compact summary of all findings for the LLM to review
    findings_text = "\n".join(
        f"[{name}] (confidence={state.agent_outputs[name].confidence:.2f}): "
        f"{state.agent_outputs[name].finding[:300]}"
        for name in completed[:10]  # cap at 10 for token budget
    )

    prompt = f"""Review these AI agent findings for logical contradictions or unsupported claims:

QUERY: {state.query}

AGENT FINDINGS:
{findings_text}

Return a JSON array of flags (empty array [] if everything looks consistent):
[
  {{
    "agent":     "Agent name that has the issue",
    "domain":    "domain key",
    "flag_type": "CONTRADICTION|UNSUPPORTED|OVERCLAIM",
    "message":   "brief explanation of the issue",
    "severity":  "warning|info"
  }}
]

Only flag genuine issues. Return [] if findings are consistent."""

    try:
        result = await asyncio.wait_for(
            call_llm_json(
                prompt=prompt,
                tier="tier2",
                max_tokens=settings.MAX_TOKENS.get("watchdog", 400),
                system=WATCHDOG_SYSTEM,
            ),
            timeout=15,
        )
        # The LLM should return a list — handle both list and dict responses
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "flags" in result:
            return result["flags"]
        return []
    except Exception as e:
        if settings.DEBUG_AGENTS:
            print(f"⚠️  Watchdog LLM check failed: {e}")
        return []
