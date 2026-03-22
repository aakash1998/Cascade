"""
agents/connector.py — Builds the causal ripple chain from agent outputs
========================================================================
The Connector is the most important synthesis agent. It reads all
domain agent outputs and constructs the "ripple chain" — a graph of
cause-effect relationships showing how Event A triggers Effect B
which triggers Effect C, and so on.

Example ripple chain for "US-China trade war":
  Trade Tariffs → Supply Chain Disruption (confidence: 0.89, 1-2 months)
  Supply Chain  → Manufacturing Slowdown  (confidence: 0.81, 2-4 months)
  Manufacturing → Labour Market Weakness   (confidence: 0.73, 3-6 months)
  Energy Costs  → Inflation Pressure       (confidence: 0.79, 1-3 months)
  Inflation     → Consumer Spending Drop   (confidence: 0.68, 3-6 months)

Each link is a RippleLink object stored in state.ripple_chain.

Tier: tier1 (Claude Haiku) — complex multi-step reasoning needed
Streaming: the plain-text ripple chain narrative is streamed token by
           token to the frontend so users see it build in real time.
"""

import asyncio
import json

from config import settings
from llm.providers import call_llm_json, call_llm_stream
from graph.state import CascadeState, RippleLink


CONNECTOR_SYSTEM = """You are a systems analyst specialising in causal chain mapping.
You identify how events in one domain propagate through connected domains,
creating ripple effects that compound over time.
You are rigorous, evidence-based, and specific about timeframes and confidence levels.
Respond with valid JSON only unless asked for narrative text."""


async def run_connector(state: CascadeState) -> CascadeState:
    """
    Builds the ripple chain from all completed domain agent outputs.
    Populates state.ripple_chain with RippleLink objects.
    """
    completed = state.get_completed_agents()
    if not completed:
        state.ripple_chain = []
        return state

    if settings.DEBUG_AGENTS:
        print(f"🔗 Connector building ripple chain from {len(completed)} agents...")

    # Build agent findings summary for the LLM
    findings_block = _build_findings_block(state, completed)

    prompt = f"""Build the causal ripple chain for this event:

QUERY: {state.query}

DOMAIN AGENT FINDINGS:
{findings_block}

For each cause-effect relationship you can identify between domains, create a ripple link.
Focus on the strongest, most certain connections first.

Return JSON:
{{
  "ripple_chain": [
    {{
      "from_domain": "source domain name",
      "to_domain":   "target domain name",
      "mechanism":   "plain English explanation of HOW domain A causes effect in domain B (1-2 sentences with specifics)",
      "confidence":  0.0-1.0,
      "timeframe":   "when this link activates (e.g. '1-2 months', '6-12 months')",
      "tier":        1 or 2 or 3  (1=direct, 2=one-step-removed, 3=distant)
    }}
  ]
}}

Guidelines:
- Tier 1: direct, immediate connections (0-2 months)
- Tier 2: secondary ripples through an intermediate domain (2-6 months)
- Tier 3: distant/long-term effects (6+ months)
- Confidence should reflect data evidence: >0.8 only if strongly supported
- Aim for 6-12 links that tell a coherent story
- Include both forward ripples (worsening) and potential dampening effects"""

    try:
        data = await asyncio.wait_for(
            call_llm_json(
                prompt=prompt,
                tier="tier1",
                max_tokens=settings.MAX_TOKENS.get("connector", 1200),
                system=CONNECTOR_SYSTEM,
            ),
            timeout=30,
        )

        raw_links = data.get("ripple_chain", [])
        links = []
        for item in raw_links:
            links.append(RippleLink(
                from_domain= str(item.get("from_domain", "")),
                to_domain=   str(item.get("to_domain",   "")),
                mechanism=   str(item.get("mechanism",   "")),
                confidence=  max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
                timeframe=   str(item.get("timeframe", "unknown")),
                tier=        int(item.get("tier", 2)),
            ))

        state.ripple_chain = links
        state.mark_phase_complete("synthesis")

        if settings.DEBUG_AGENTS:
            print(f"✅ Connector: {len(links)} ripple links built")

    except Exception as e:
        print(f"❌ Connector failed: {e}")
        state.add_error("Connector", "synthesis", str(e))
        state.ripple_chain = []

    return state


async def stream_ripple_narrative(state: CascadeState):
    """
    Streams a plain-language narrative of the ripple chain token by token.
    Used by the pipeline to yield SSE 'chain_token' events to the frontend.

    Yields: str tokens
    """
    if not state.ripple_chain:
        yield "The ripple chain could not be constructed for this query."
        return

    # Format the chain for the narrative prompt
    chain_text = "\n".join(
        f"  {i+1}. {link.from_domain} → {link.to_domain}: {link.mechanism} "
        f"({link.timeframe}, {link.confidence:.0%} confidence)"
        for i, link in enumerate(state.ripple_chain[:10])
    )

    profile_str = state.profile.to_prompt_string()
    user_context = f"\nUser profile: {profile_str}" if not state.profile.is_empty() else ""

    narrative_prompt = f"""Write a clear, flowing narrative explaining this ripple chain of effects:

ORIGINAL EVENT: {state.query}
{user_context}

CAUSAL CHAIN:
{chain_text}

Write 3-4 paragraphs in plain English that:
1. Explain the direct impact of the event
2. Show how effects ripple through connected domains
3. Explain the timeline (what hits first, what follows later)
4. Note the biggest uncertainty in the chain

Write for a general audience — no jargon. Make it engaging and specific."""

    try:
        async for token in call_llm_stream(
            prompt=narrative_prompt,
            tier="tier1",
            max_tokens=600,
            system="You are a skilled economics journalist who explains complex ripple effects clearly and engagingly.",
        ):
            yield token
    except Exception as e:
        yield f"\n[Narrative generation failed: {e}]"


def _build_findings_block(state: CascadeState, completed: list[str]) -> str:
    """Formats agent findings into a compact block for the connector prompt."""
    lines = []
    # Sort by confidence descending — show strongest signals first
    sorted_agents = sorted(
        completed,
        key=lambda n: state.agent_outputs[n].confidence,
        reverse=True,
    )
    for name in sorted_agents[:12]:
        output = state.agent_outputs[name]
        downstream = ", ".join(output.downstream_signals[:4]) or "none identified"
        lines.append(
            f"[{output.domain.upper()}] (confidence={output.confidence:.2f})\n"
            f"  Finding: {output.finding[:250]}\n"
            f"  Timeframe: {output.timeframe}\n"
            f"  Downstream signals: {downstream}\n"
            f"  Severity: {output.severity}"
        )
    return "\n\n".join(lines)
