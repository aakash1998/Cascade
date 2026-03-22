"""
agents/personaliser.py — Applies user profile to the ripple chain
==================================================================
The Personaliser takes the full ripple chain analysis and translates
it into a personalised impact statement for this specific user.

"What does all this mean for ME?"

Without personalisation: "Tech sector hiring will slow."
With personalisation: "As a software engineer in Calgary earning $60-100k
with a family and mortgage, here's what this means: your employer may
freeze headcount, your mortgage renewals may coincide with peak rates,
and your USD savings actually hedge some of the downside..."

The Personaliser reads:
  - state.profile (the user's onboarding answers)
  - state.ripple_chain (the causal chain)
  - state.scenarios (best/base/worst)
  - state.agent_outputs (the raw domain findings)

And produces state.personal_impact — a streaming, personalised narrative.

Tier: tier1 (Claude Haiku) — personalisation needs nuanced reasoning
Streaming: the output is streamed token by token to the frontend
"""

import asyncio

from config import settings
from llm.providers import call_llm_stream
from graph.state import CascadeState


PERSONALISER_SYSTEM = """You are a personal financial advisor and life coach with deep expertise
in macroeconomics. You translate complex global events into specific, actionable personal impact
for individual people. You are warm, direct, and specific — not generic.
Never say "it depends" without also saying "and here's the most likely direction for you personally."
Speak in second person ("you", "your")."""


async def run_personaliser(state: CascadeState) -> CascadeState:
    """
    Generates the personalised impact narrative and populates state.personal_impact.
    Uses streaming internally but collects the full text for state storage.
    """
    if state.profile.is_empty():
        state.personal_impact = (
            "No personal profile was provided. "
            "Set your profile to get a personalised impact analysis tailored to your job, "
            "location, household, and financial situation."
        )
        return state

    # Collect streaming output into state.personal_impact
    tokens = []
    try:
        async for token in stream_personal_impact(state):
            tokens.append(token)
        state.personal_impact = "".join(tokens)
    except Exception as e:
        print(f"⚠️  Personaliser failed: {e}")
        state.add_error("Personaliser", "personalisation", str(e))
        state.personal_impact = "Personal impact analysis could not be generated."

    return state


async def stream_personal_impact(state: CascadeState):
    """
    Streams the personalised impact narrative token by token.
    Used by the pipeline to yield SSE 'personal_token' events.

    Yields: str tokens
    """
    profile = state.profile
    profile_str = profile.to_prompt_string()

    # Build a summary of relevant ripple chain elements
    chain_summary = _build_relevant_chain(state)
    scenario_summary = _build_scenario_summary(state)

    prompt = f"""Write a personalised impact analysis for this specific person:

USER PROFILE: {profile_str}

ORIGINAL EVENT: {state.query}

HOW THIS EVENT RIPPLES:
{chain_summary}

THREE SCENARIOS:
{scenario_summary}

Write 3-4 paragraphs specifically for this person:

Paragraph 1: The most direct impact on their job/income/sector — what happens to their industry and employer?

Paragraph 2: The impact on their cost of living — housing, mortgage/rent, everyday expenses, and inflation.

Paragraph 3: What they should watch for and the 1-2 most important actions they could take to protect themselves or benefit.

Paragraph 4 (optional): Wild card — one unexpected way this event could affect them that they might not have considered.

Be specific to their profile. If they're a software engineer in Calgary, say "Calgary tech companies" not "technology companies generally."
Reference their income bracket, household type, and housing situation.
Do not hedge excessively — give your best assessment with appropriate confidence."""

    try:
        async for token in call_llm_stream(
            prompt=prompt,
            tier="tier1",
            max_tokens=settings.MAX_TOKENS.get("personaliser", 700),
            system=PERSONALISER_SYSTEM,
        ):
            yield token
    except Exception as e:
        yield f"\n[Personalisation failed: {e}]"


def _build_relevant_chain(state: CascadeState) -> str:
    """Builds a compact chain summary relevant to the user's profile."""
    profile = state.profile

    lines = []
    # All ripple links
    for link in state.ripple_chain[:8]:
        lines.append(
            f"• {link.from_domain} → {link.to_domain}: {link.mechanism[:150]} "
            f"({link.timeframe}, {link.confidence:.0%} confidence)"
        )

    # Especially relevant domains based on profile
    relevant_domains = _get_relevant_domains(profile)
    if relevant_domains:
        lines.append(f"\nMost relevant to this person: {', '.join(relevant_domains)}")

    return "\n".join(lines) or "No ripple chain data available."


def _build_scenario_summary(state: CascadeState) -> str:
    """Compact scenario summary for the personaliser prompt."""
    if not state.scenarios:
        return "No scenarios available."
    lines = []
    for s in state.scenarios:
        lines.append(f"  {s.display_name} ({s.probability} probability): {s.ripple_summary[:200]}")
    return "\n".join(lines)


def _get_relevant_domains(profile) -> list:
    """Returns domain names most relevant to the user's profile."""
    domains = []
    if profile.job:
        job_lower = profile.job.lower()
        if any(w in job_lower for w in ["engineer", "developer", "tech", "software", "data"]):
            domains.append("technology")
        if any(w in job_lower for w in ["nurse", "doctor", "health", "medical"]):
            domains.append("healthcare")
        if any(w in job_lower for w in ["teacher", "professor", "school"]):
            domains.append("education")
        domains.append("labour")

    if profile.housing in ["Own with mortgage", "mortgage"]:
        domains.extend(["housing", "finance"])

    if profile.income_bracket:
        domains.append("inflation")

    return list(dict.fromkeys(domains))[:4]  # dedup, cap at 4
