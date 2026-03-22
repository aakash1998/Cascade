"""
agents/orchestrator.py — The Orchestrator Agent
=================================================
The Orchestrator is the first agent that runs for every query.
It does NOT answer the question. Its only job is to read the
question and decide who should answer it.

What it does:
  1. Reads the user's query and profile
  2. Detects the query intent (personal impact? prediction? causal?)
  3. Scores complexity across 5 dimensions (1.0 - 5.0 each)
  4. Decides which domain agents are needed (the "manifest")
  5. Returns a structured JSON plan for the pipeline to execute

Why this matters:
  Without an orchestrator, you'd always spin up all 23 agents
  for every query — even simple ones. That wastes money and time.

  "What does a Fed rate cut mean for me?" needs 5 agents.
  "How do AI layoffs, inflation, and the Middle East war connect?"
  needs 22 agents. The orchestrator knows the difference.

Output — the manifest:
  {
    "complexity": {
      "geographic_scope": 4.0,
      "domain_breadth": 3.5,
      "causal_depth": 3.0,
      "time_horizon": 2.0,
      "personal_relevance": 4.5,
      "total": 3.5,
      "agent_count": 16
    },
    "query_intent": "personal_impact",
    "reasoning": "Query involves trade policy affecting a specific...",
    "agents": [
      {"name": "Trade Agent",    "tier": 1, "focus": "US-China tariffs on tech"},
      {"name": "Labour Agent",   "tier": 2, "focus": "tech hiring in Canada"},
      {"name": "Inflation Agent","tier": 2, "focus": "consumer price impact"},
      ...
    ]
  }

Usage:
  from agents.orchestrator import run_orchestrator
  from graph.state import CascadeState

  state = create_initial_state(query="...", profile={...})
  updated_state = await run_orchestrator(state)
  print(updated_state.manifest.agents)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timezone

from config import settings
from graph.state import (
    CascadeState,
    AgentManifest,
    ComplexityScore,
    create_initial_state,
)
from llm.providers import call_llm_json


# ─────────────────────────────────────────────
# ALL AVAILABLE DOMAIN AGENTS
# ─────────────────────────────────────────────
# This is the full list of conditional agents the orchestrator
# can choose from. Each has a name, the keywords that trigger it,
# and example focus areas.

AVAILABLE_AGENTS = [
    {
        "name": "Energy Agent",
        "domain": "energy",
        "triggers": ["oil", "gas", "energy", "opec", "electricity", "fuel",
                     "renewables", "coal", "pipeline", "nuclear"],
        "description": "Oil prices, gas supply, energy policy, renewables transition",
    },
    {
        "name": "Trade Agent",
        "domain": "trade",
        "triggers": ["trade", "tariff", "import", "export", "tariffs", "sanctions",
                     "wto", "supply chain", "manufacturing", "goods"],
        "description": "Tariffs, trade wars, import/export flows, sanctions",
    },
    {
        "name": "Labour Agent",
        "domain": "labour",
        "triggers": ["job", "jobs", "employment", "unemployment", "layoff", "layoffs",
                     "hiring", "wages", "workers", "workforce", "automation"],
        "description": "Employment, layoffs, wages, automation, labour market",
    },
    {
        "name": "Inflation Agent",
        "domain": "inflation",
        "triggers": ["inflation", "prices", "cpi", "cost of living", "purchasing power",
                     "interest rate", "interest rates", "fed", "central bank"],
        "description": "Consumer prices, CPI, purchasing power, interest rates",
    },
    {
        "name": "Geopolitics Agent",
        "domain": "geopolitics",
        "triggers": ["war", "conflict", "military", "sanctions", "election", "elections",
                     "government", "diplomacy", "nato", "un", "treaty", "politics"],
        "description": "Wars, conflicts, elections, diplomatic tensions, alliances",
    },
    {
        "name": "Currency Agent",
        "domain": "currency",
        "triggers": ["currency", "dollar", "exchange rate", "forex", "devaluation",
                     "usd", "eur", "cad", "yuan", "yen", "pound", "reserves"],
        "description": "Exchange rates, forex movements, currency reserves",
    },
    {
        "name": "Supply Chain Agent",
        "domain": "supply_chain",
        "triggers": ["supply chain", "shipping", "logistics", "port", "freight",
                     "manufacturing", "semiconductor", "chips", "factory"],
        "description": "Shipping, logistics, port activity, manufacturing disruption",
    },
    {
        "name": "Technology Agent",
        "domain": "technology",
        "triggers": ["tech", "ai", "artificial intelligence", "semiconductor", "chips",
                     "software", "cyber", "patent", "innovation", "startup"],
        "description": "AI, semiconductors, cybersecurity, tech regulation",
    },
    {
        "name": "Housing Agent",
        "domain": "housing",
        "triggers": ["housing", "real estate", "mortgage", "rent", "property",
                     "home", "construction", "interest rate"],
        "description": "Real estate, mortgages, rent, housing market",
    },
    {
        "name": "Healthcare Agent",
        "domain": "healthcare",
        "triggers": ["health", "healthcare", "medical", "pharma", "drug", "pandemic",
                     "hospital", "insurance", "disease"],
        "description": "Public health, pharmaceuticals, healthcare costs",
    },
    {
        "name": "Climate Agent",
        "domain": "climate",
        "triggers": ["climate", "weather", "carbon", "emissions", "green", "esg",
                     "flood", "drought", "hurricane", "disaster", "environment"],
        "description": "Climate policy, extreme weather, energy transition",
    },
    {
        "name": "Food Agent",
        "domain": "food",
        "triggers": ["food", "agriculture", "crop", "wheat", "grain", "famine",
                     "fertilizer", "farming", "commodity"],
        "description": "Food prices, agriculture, supply disruptions, famine",
    },
    {
        "name": "Finance Agent",
        "domain": "finance",
        "triggers": ["market", "stock", "bank", "banking", "debt", "recession",
                     "gdp", "economy", "financial", "credit", "bonds"],
        "description": "Financial markets, banking sector, sovereign debt, recession",
    },
    {
        "name": "Migration Agent",
        "domain": "migration",
        "triggers": ["migration", "immigration", "refugee", "population", "border",
                     "emigration", "diaspora", "displacement"],
        "description": "Population movement, immigration policy, refugee flows",
    },
    {
        "name": "Social Agent",
        "domain": "social",
        "triggers": ["social", "protest", "inequality", "polarization", "unrest",
                     "media", "sentiment", "public opinion", "society"],
        "description": "Social sentiment, protests, inequality, polarisation",
    },
    {
        "name": "Mental Health Agent",
        "domain": "mental_health",
        "triggers": ["mental health", "anxiety", "depression", "wellbeing",
                     "addiction", "suicide", "stress", "burnout"],
        "description": "Mental health trends, wellbeing impacts, addiction",
    },
    {
        "name": "Education Agent",
        "domain": "education",
        "triggers": ["education", "school", "university", "student", "tuition",
                     "skills", "learning", "degree"],
        "description": "Education access, student debt, skills gaps",
    },
    {
        "name": "Crime Agent",
        "domain": "crime",
        "triggers": ["crime", "security", "safety", "police", "violence",
                     "corruption", "fraud", "cybercrime"],
        "description": "Crime rates, security, corruption, social stability",
    },
    {
        "name": "Debt Agent",
        "domain": "debt",
        "triggers": ["debt", "credit", "bankruptcy", "loan", "mortgage",
                     "borrowing", "default", "deficit"],
        "description": "Personal debt, credit access, bankruptcies, sovereign debt",
    },
    {
        "name": "Media Agent",
        "domain": "media",
        "triggers": ["media", "news", "misinformation", "propaganda", "censorship",
                     "social media", "narrative", "disinformation"],
        "description": "Media narratives, misinformation, propaganda, censorship",
    },
    {
        "name": "Demographics Agent",
        "domain": "demographics",
        "triggers": ["population", "aging", "birth rate", "demographics",
                     "workforce", "generation", "elderly"],
        "description": "Population changes, aging societies, birth rates",
    },
    {
        "name": "Infrastructure Agent",
        "domain": "infrastructure",
        "triggers": ["infrastructure", "power grid", "internet", "water",
                     "roads", "bridge", "utilities"],
        "description": "Power grids, internet, water, transportation infrastructure",
    },
    {
        "name": "Culture Agent",
        "domain": "culture",
        "triggers": ["religion", "culture", "identity", "values", "tradition",
                     "nationalism", "community"],
        "description": "Cultural tensions, identity politics, religious conflict",
    },
]


# ─────────────────────────────────────────────
# COMPLEXITY WEIGHTS
# ─────────────────────────────────────────────

COMPLEXITY_WEIGHTS = {
    "geographic_scope":   0.20,
    "domain_breadth":     0.30,  # most important
    "causal_depth":       0.25,
    "time_horizon":       0.10,
    "personal_relevance": 0.15,
}


def _agent_count_from_score(total: float) -> int:
    """
    Maps a complexity total score (1.0-5.0) to
    the number of conditional domain agents to spawn.

    The 10 permanent agents always run on top of this.
    """
    if total <= 2.0: return 3
    if total <= 3.0: return 8
    if total <= 4.0: return 14
    return min(23, int(total * 5))


# ─────────────────────────────────────────────
# ORCHESTRATOR PROMPT
# ─────────────────────────────────────────────

ORCHESTRATOR_SYSTEM = """You are the Orchestrator for Cascade, a ripple effect analysis engine.

Your job is to analyse a user's query and return a JSON plan.
You do NOT answer the question. You decide WHO should answer it.

You must return ONLY valid JSON — no explanation, no markdown.

Available domain agents and their triggers:
{agent_list}

User profile (may be empty):
{profile}

Return this exact JSON structure:
{{
  "complexity": {{
    "geographic_scope": <1.0-5.0>,
    "domain_breadth": <1.0-5.0>,
    "causal_depth": <1.0-5.0>,
    "time_horizon": <1.0-5.0>,
    "personal_relevance": <1.0-5.0>
  }},
  "query_intent": "<personal_impact|prediction|causal_chain|historical|comparison|counterfactual|general>",
  "reasoning": "<one sentence explaining your choices>",
  "agents": [
    {{
      "name": "<exact agent name from list>",
      "tier": <1 or 2>,
      "focus": "<specific aspect to focus on for this query>"
    }}
  ]
}}

Scoring guide:
  geographic_scope:   1=local, 3=regional, 5=global
  domain_breadth:     number of sectors affected × 0.5 (max 5.0)
  causal_depth:       1=direct impact, 3=2 steps removed, 5=3+ steps
  time_horizon:       1=days, 3=months, 5=years+
  personal_relevance: 1=no profile match, 3=partial match, 5=direct match

Tier guide:
  tier 1 = most important agents for this query (max 3)
  tier 2 = supporting agents

Only include agents that are genuinely relevant.
Do not include agents just to have more agents.
"""

ORCHESTRATOR_USER = """Query: {query}

Analyse this query and return the JSON plan."""


# ─────────────────────────────────────────────
# KEYWORD PRE-FILTER
# ─────────────────────────────────────────────

def _keyword_prefilter(query: str) -> list[str]:
    """
    Quick keyword scan to pre-select likely relevant agents.
    This gives the LLM a shorter, focused list to choose from
    rather than all 23 agents — saves tokens and improves accuracy.

    Returns a list of agent names that match at least one keyword.
    Always includes a minimum set of core agents.
    """
    query_lower = query.lower()
    matched = []

    for agent in AVAILABLE_AGENTS:
        for trigger in agent["triggers"]:
            if trigger in query_lower:
                matched.append(agent["name"])
                break

    # Always include these core agents regardless of keywords
    # They are relevant to almost every world event query
    core_always = ["Finance Agent", "Trade Agent", "Geopolitics Agent"]
    for core in core_always:
        if core not in matched:
            matched.append(core)

    return matched


# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR FUNCTION
# ─────────────────────────────────────────────

async def run_orchestrator(state: CascadeState) -> CascadeState:
    """
    Runs the Orchestrator agent on the current state.

    Reads: state.query, state.profile
    Writes: state.manifest, state.complexity, state.query_intent

    Args:
        state: The current pipeline state

    Returns:
        Updated state with manifest filled in

    This is called as the first node in the LangGraph pipeline.
    """
    state.current_phase = "planning"

    try:
        # Step 1: Get keyword-matched agents to give LLM a focused list
        prefiltered = _keyword_prefilter(state.query)

        # Build agent list string for the prompt
        agent_list_str = "\n".join([
            f"- {a['name']}: {a['description']}"
            for a in AVAILABLE_AGENTS
            if a['name'] in prefiltered
        ])

        # Build profile string
        profile_str = state.profile.to_prompt_string()

        # Step 2: Call LLM to get the manifest
        prompt = ORCHESTRATOR_USER.format(query=state.query)
        system = ORCHESTRATOR_SYSTEM.format(
            agent_list=agent_list_str,
            profile=profile_str,
        )

        if settings.DEBUG_AGENTS:
            print(f"\n🎯 Orchestrator running for: {state.query[:60]}...")
            print(f"   Pre-filtered agents: {prefiltered}")

        # Use tier1 (Claude) for orchestration — reliable JSON is critical here
        raw_manifest = await call_llm_json(
            prompt=prompt,
            system=system,
            tier="tier1",
            max_tokens=settings.MAX_TOKENS["orchestrator"],
        )

        # Step 3: Parse and validate the manifest
        manifest, complexity = _parse_manifest(raw_manifest)

        # Step 4: Apply complexity cap from config
        if complexity.total > settings.MAX_COMPLEXITY:
            complexity.total = settings.MAX_COMPLEXITY
            complexity.agent_count = _agent_count_from_score(settings.MAX_COMPLEXITY)

        # Step 5: Write to state
        state.manifest = manifest
        state.complexity = complexity
        state.query_intent = raw_manifest.get("query_intent", "general")
        state.mark_phase_complete("planning")

        if settings.DEBUG_AGENTS:
            print(f"   Complexity: {complexity.to_display_string()}")
            print(f"   Intent: {state.query_intent}")
            print(f"   Agents selected: {[a['name'] for a in manifest.agents]}")

    except Exception as e:
        # Orchestrator failed — fall back to minimal safe manifest
        error_msg = f"Orchestrator failed: {str(e)}"
        state.add_error("Orchestrator", "planning", error_msg)
        print(f"⚠️  {error_msg} — using fallback manifest")

        state.manifest = _fallback_manifest(state.query)
        state.complexity = ComplexityScore(total=2.0, agent_count=5)

    return state


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _parse_manifest(raw: dict) -> tuple[AgentManifest, ComplexityScore]:
    """
    Parses the raw JSON from the LLM into typed objects.
    Handles missing fields gracefully with safe defaults.
    """
    # Parse complexity scores
    comp_raw = raw.get("complexity", {})
    geo   = float(comp_raw.get("geographic_scope",   1.0))
    dom   = float(comp_raw.get("domain_breadth",     1.0))
    depth = float(comp_raw.get("causal_depth",       1.0))
    time  = float(comp_raw.get("time_horizon",       1.0))
    pers  = float(comp_raw.get("personal_relevance", 1.0))

    # Clamp all values to 1.0-5.0
    geo   = max(1.0, min(5.0, geo))
    dom   = max(1.0, min(5.0, dom))
    depth = max(1.0, min(5.0, depth))
    time  = max(1.0, min(5.0, time))
    pers  = max(1.0, min(5.0, pers))

    # Calculate weighted total
    total = (
        geo   * COMPLEXITY_WEIGHTS["geographic_scope"]   +
        dom   * COMPLEXITY_WEIGHTS["domain_breadth"]     +
        depth * COMPLEXITY_WEIGHTS["causal_depth"]       +
        time  * COMPLEXITY_WEIGHTS["time_horizon"]       +
        pers  * COMPLEXITY_WEIGHTS["personal_relevance"]
    )
    total = round(total, 2)
    agent_count = _agent_count_from_score(total)

    complexity = ComplexityScore(
        geographic_scope=geo,
        domain_breadth=dom,
        causal_depth=depth,
        time_horizon=time,
        personal_relevance=pers,
        total=total,
        agent_count=agent_count,
    )

    # Validate agents against known list
    valid_names = {a["name"] for a in AVAILABLE_AGENTS}
    agents = []
    for agent_raw in raw.get("agents", []):
        name = agent_raw.get("name", "")
        if name in valid_names:
            agents.append({
                "name":  name,
                "tier":  int(agent_raw.get("tier", 2)),
                "focus": agent_raw.get("focus", ""),
            })

    # Ensure we have at least 3 agents
    if len(agents) < 3:
        agents = _fallback_manifest("").agents

    manifest = AgentManifest(
        agents=agents[:agent_count],   # cap at calculated agent count
        complexity=complexity,
        query_intent=raw.get("query_intent", "general"),
        reasoning=raw.get("reasoning", ""),
    )

    return manifest, complexity


def _fallback_manifest(query: str) -> AgentManifest:
    """
    Returns a safe minimal manifest when the orchestrator fails.
    Uses keyword matching only — no LLM involved.
    Always gives at least a useful analysis even if orchestrator errors.
    """
    prefiltered = _keyword_prefilter(query)

    agents = [
        {"name": name, "tier": 2, "focus": "general analysis"}
        for name in prefiltered[:5]
    ]

    return AgentManifest(
        agents=agents,
        complexity=ComplexityScore(total=2.0, agent_count=5),
        query_intent="general",
        reasoning="Fallback manifest — orchestrator unavailable",
    )


# ─────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test the orchestrator with a real query:
      python -m agents.orchestrator
    """
    import asyncio

    async def test():
        print("\n🧪 Testing Orchestrator...\n")

        # Test query 1 — medium complexity
        query1 = "What does the US-China trade war mean for a software engineer in Calgary?"
        profile1 = {
            "job":    "Software engineer",
            "city":   "Calgary, Canada",
            "sector": "Tech",
        }

        state1 = create_initial_state(
            query=query1,
            session_id="test-001",
            profile=profile1,
        )

        print(f"Query: {query1[:60]}...")
        print("Running orchestrator...")

        state1 = await run_orchestrator(state1)

        print(f"\n✅ Orchestrator complete")
        print(f"   Complexity:  {state1.complexity.to_display_string()}")
        print(f"   Intent:      {state1.query_intent}")
        print(f"   Reasoning:   {state1.manifest.reasoning}")
        print(f"\n   Agents selected ({len(state1.manifest.agents)}):")
        for agent in state1.manifest.agents:
            tier_label = "⭐ Tier 1" if agent['tier'] == 1 else "   Tier 2"
            print(f"     {tier_label} — {agent['name']}: {agent['focus'][:50]}")

        print(f"\n   Errors: {len(state1.errors)}")
        if state1.errors:
            for e in state1.errors:
                print(f"     ⚠️  {e.message}")

        print("\n✅ Orchestrator test complete\n")

    asyncio.run(test())