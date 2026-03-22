"""
agents/summariser.py — Final plain-language summary generator
=============================================================
The Summariser is the last agent in the pipeline. It reads the complete
analysis and distills it into a concise, accessible summary that
non-experts can understand.

The summary answers: "If I could only read one thing, what are the
three most important takeaways from this entire analysis?"

The Summariser:
  1. Reads all agent findings, the ripple chain, and scenarios
  2. Identifies the 3 most important insights
  3. Writes them in clear, jargon-free language
  4. Adds a confidence level and key uncertainty caveat
  5. Streams the result token-by-token to the frontend

Tier: tier2 (Groq) — summarisation doesn't need Claude-level reasoning
Streaming: output is streamed token by token for live display
"""

import asyncio

from config import settings
from llm.providers import call_llm_stream
from graph.state import CascadeState


SUMMARISER_SYSTEM = """You are a world-class economic journalist who can take complex,
multi-domain analysis and distill it into three crisp, insightful takeaways
that a general reader can understand and act on.
You are direct, concrete, and never use jargon without explaining it."""


async def run_summariser(state: CascadeState) -> CascadeState:
    """
    Generates the final summary and populates state.summary.
    Collects streaming tokens into a complete string.
    """
    tokens = []
    try:
        async for token in stream_summary(state):
            tokens.append(token)
        state.summary = "".join(tokens)
        state.mark_phase_complete("output")
    except Exception as e:
        print(f"⚠️  Summariser failed: {e}")
        state.add_error("Summariser", "output", str(e))
        state.summary = _fallback_summary(state)

    return state


async def stream_summary(state: CascadeState):
    """
    Streams the final summary token by token.
    Used by the pipeline to yield SSE 'summary_token' events.

    Yields: str tokens
    """
    # Build a compact overview of everything for the LLM
    overview = _build_full_overview(state)
    profile_str = state.profile.to_prompt_string()

    prompt = f"""You have completed a multi-agent analysis of this event:

EVENT: {state.query}
USER PROFILE: {profile_str if not state.profile.is_empty() else "General audience"}

FULL ANALYSIS OVERVIEW:
{overview}

Write the final summary with exactly this structure:

**The Big Picture**
[2-3 sentences: what is fundamentally happening and why it matters]

**3 Key Takeaways**
1. [Most important finding with specific timeframe and confidence level]
2. [Second most important, especially if counterintuitive]
3. [Third takeaway — could be the timeline, a wild card, or what to watch]

**The Main Uncertainty**
[1 sentence: the single biggest unknown that could change the whole picture]

**Bottom Line**
[1 sentence: the most actionable conclusion]

Use plain English. No jargon. Be specific — include numbers, timeframes, and domain names.
If the analysis has high confidence (>{int(state.overall_confidence*100)}%), say so."""

    try:
        async for token in call_llm_stream(
            prompt=prompt,
            tier="tier2",
            max_tokens=settings.MAX_TOKENS.get("summariser", 400),
            system=SUMMARISER_SYSTEM,
        ):
            yield token
    except Exception as e:
        yield f"\n[Summary generation failed: {e}]"


def _build_full_overview(state: CascadeState) -> str:
    """Builds a compact overview of the entire analysis for the summariser prompt."""
    sections = []

    # Top agent findings
    completed = state.get_completed_agents()
    if completed:
        findings = sorted(
            completed,
            key=lambda n: state.agent_outputs[n].confidence,
            reverse=True,
        )
        lines = ["Agent Findings (top 6 by confidence):"]
        for name in findings[:6]:
            out = state.agent_outputs[name]
            lines.append(
                f"  [{out.domain}] {out.finding[:180]} "
                f"(conf={out.confidence:.0%}, {out.timeframe})"
            )
        sections.append("\n".join(lines))

    # Ripple chain highlights
    if state.ripple_chain:
        lines = ["Key Ripple Links:"]
        for link in state.ripple_chain[:5]:
            lines.append(f"  {link.from_domain} → {link.to_domain}: {link.mechanism[:120]}")
        sections.append("\n".join(lines))

    # Scenario summaries
    if state.scenarios:
        lines = ["Scenarios:"]
        for s in state.scenarios:
            lines.append(f"  {s.display_name} ({s.probability}): {s.ripple_summary[:120]}")
        sections.append("\n".join(lines))

    # Historical context
    if state.historical_parallels:
        p = state.historical_parallels[0]
        sections.append(
            f"Historical Parallel: {p.get('event', '')} ({p.get('year', '')}) — "
            f"{p.get('outcome', '')[:120]}"
        )

    # Overall confidence
    sections.append(
        f"Overall confidence: {state.overall_confidence:.0%} | "
        f"Agents: {len(completed)}/{state.manifest.complexity.agent_count} | "
        f"Flags: {len(state.hallucination_flags)}"
    )

    return "\n\n".join(sections)


def _fallback_summary(state: CascadeState) -> str:
    """Emergency fallback if LLM summary fails — uses raw data."""
    completed = state.get_completed_agents()
    if not completed:
        return "Analysis could not be completed for this query."

    lines = [f"Summary of analysis for: {state.query[:100]}\n"]
    for name in completed[:3]:
        out = state.agent_outputs[name]
        lines.append(f"• {out.domain.title()}: {out.finding[:200]}")

    if state.ripple_chain:
        first = state.ripple_chain[0]
        lines.append(f"\nKey ripple: {first.from_domain} → {first.to_domain}: {first.mechanism[:150]}")

    return "\n".join(lines)
