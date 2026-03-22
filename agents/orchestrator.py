"""
agents/orchestrator.py — Query analyser + agent planner
=========================================================
The Orchestrator is the first agent to run. It reads the user's query
and decides:

  1. COMPLEXITY SCORE — 5-dimensional scoring that determines how many
     agents to spin up (1-33 agents based on how complex the query is)

  2. AGENT MANIFEST — the specific list of domain agents to run,
     each with a tailored focus area

  3. QUERY INTENT — classifies the query type so downstream agents
     know how to frame their answers

Tier: tier1 (Claude Haiku) — orchestration needs reliable structured JSON
      Falls back to Groq if Claude unavailable

The manifest output looks like:
  [
    {"name": "Energy Agent",   "tier": 1, "focus": "OPEC production and oil price trajectory"},
    {"name": "Labour Agent",   "tier": 2, "focus": "Canadian tech job market impact"},
    {"name": "Finance Agent",  "tier": 2, "focus": "Credit market tightening"},
    ...
  ]
"""

import json
from typing import Any

from config import settings
from llm.providers import call_llm_json
from graph.state import (
    CascadeState, ComplexityScore, AgentManifest
)

# ─────────────────────────────────────────────
# ALL AVAILABLE DOMAIN AGENTS
# Each entry: (agent_key, display_name, description)
# ─────────────────────────────────────────────

AVAILABLE_DOMAINS = [
    ("energy",          "Energy Agent",           "Oil, gas, renewables, power grids, OPEC"),
    ("trade",           "Trade Agent",            "Tariffs, exports, imports, WTO, trade deficits"),
    ("labour",          "Labour Agent",           "Jobs, hiring, wages, unemployment, automation"),
    ("finance",         "Finance Agent",          "Banks, credit, interest rates, stock markets"),
    ("inflation",       "Inflation Agent",        "Prices, CPI, purchasing power, cost of living"),
    ("supply_chain",    "Supply Chain Agent",     "Manufacturing, logistics, shipping, inventory"),
    ("geopolitics",     "Geopolitics Agent",      "International relations, sanctions, alliances"),
    ("technology",      "Technology Agent",       "Tech sector, semiconductors, AI, digital"),
    ("housing",         "Housing Agent",          "Real estate, mortgages, rents, construction"),
    ("healthcare",      "Healthcare Agent",       "Medical costs, pharma, public health policy"),
    ("agriculture",     "Agriculture Agent",      "Food production, commodity prices, supply"),
    ("environment",     "Environment Agent",      "Climate, emissions, carbon markets, regulations"),
    ("currency_fx",     "Currency/FX Agent",      "Exchange rates, USD strength, forex markets"),
    ("manufacturing",   "Manufacturing Agent",    "Industrial output, factories, reshoring"),
    ("retail",          "Retail Agent",           "Consumer spending, e-commerce, brick and mortar"),
    ("government",      "Government Agent",       "Fiscal policy, taxes, regulation, stimulus"),
    ("immigration",     "Immigration Agent",      "Labour mobility, skilled workers, policy"),
    ("education",       "Education Agent",        "Skills gap, tuition, workforce training"),
    ("security",        "Security Agent",         "Defence spending, cybersecurity, military"),
    ("commodities",     "Commodities Agent",      "Metals, minerals, rare earths, soft commodities"),
    ("transportation",  "Transportation Agent",   "Shipping, aviation, freight, infrastructure"),
    ("demographics",    "Demographics Agent",     "Population, ageing, birth rates, migration"),
    ("media",           "Media Agent",            "Information flows, public opinion, narrative"),
]

ORCHESTRATOR_SYSTEM = """You are the Cascade Orchestrator — an expert geopolitical and economic analyst.
Your job is to analyse a user's query and plan which AI agents should investigate it.

You must return ONLY valid JSON — no markdown, no explanation, just the JSON object.
Every key must be present. All numeric scores must be between 1.0 and 5.0."""


def _build_orchestrator_prompt(query: str, profile_str: str, history: list) -> str:
    """Builds the orchestrator's planning prompt."""

    history_str = ""
    if history:
        recent = history[-3:]
        history_str = "\nCONVERSATION HISTORY:\n" + "\n".join(
            f"  {t.get('role','').upper()}: {t.get('content','')[:200]}"
            for t in recent
        )

    domain_list = "\n".join(
        f"  {key}: {name} — {desc}"
        for key, name, desc in AVAILABLE_DOMAINS
    )

    return f"""Analyse this query and return the planning JSON:

QUERY: {query}
USER PROFILE: {profile_str or "Not provided"}
{history_str}

AVAILABLE DOMAIN AGENTS:
{domain_list}

Return this exact JSON structure:
{{
  "query_intent": "one of: personal_impact | causal_chain | prediction | comparison | scenario | general",
  "complexity": {{
    "geographic_scope":   1.0-5.0,
    "domain_breadth":     1.0-5.0,
    "causal_depth":       1.0-5.0,
    "time_horizon":       1.0-5.0,
    "personal_relevance": 1.0-5.0,
    "total":              weighted_average_1.0-5.0,
    "agent_count":        integer_6_to_23
  }},
  "agents": [
    {{
      "key":   "domain_key_from_list_above",
      "name":  "Agent Display Name",
      "tier":  1_or_2,
      "focus": "specific_sub-question_this_agent_should_answer_about_the_query"
    }}
  ],
  "reasoning": "1-2 sentences on why you chose these agents and this complexity score"
}}

Rules:
- agent_count = round(complexity.total * 4.0 + 2), capped at 23
- tier=1 only for the 3-5 most critical agents; tier=2 for the rest
- Every selected agent must have a focus tailored to this specific query
- If user profile is provided and the query affects them, include personal_relevance >= 3.5
- Select ONLY the most relevant domains — quality over quantity"""


# ─────────────────────────────────────────────
# ORCHESTRATE FUNCTION (called from pipeline node)
# ─────────────────────────────────────────────

async def run_orchestrator(state: CascadeState) -> CascadeState:
    """
    Analyses the query and populates state.manifest and state.complexity.
    Called as the first pipeline node.

    Returns the updated state — the pipeline passes this to the next node.
    """
    profile_str = state.profile.to_prompt_string()
    prompt = _build_orchestrator_prompt(
        query=state.query,
        profile_str=profile_str,
        history=state.conversation_history,
    )

    try:
        data = await call_llm_json(
            prompt=prompt,
            tier="tier1",
            max_tokens=settings.MAX_TOKENS.get("orchestrator", 600),
            system=ORCHESTRATOR_SYSTEM,
        )

        # ── Build ComplexityScore ──────────────────────────────
        comp_data = data.get("complexity", {})
        complexity = ComplexityScore(
            geographic_scope=   float(comp_data.get("geographic_scope",   2.0)),
            domain_breadth=     float(comp_data.get("domain_breadth",     2.0)),
            causal_depth=       float(comp_data.get("causal_depth",       2.0)),
            time_horizon=       float(comp_data.get("time_horizon",       2.0)),
            personal_relevance= float(comp_data.get("personal_relevance", 2.0)),
            total=              float(comp_data.get("total",              2.0)),
            agent_count=        int(comp_data.get("agent_count",         8)),
        )
        complexity.agent_count = min(complexity.agent_count, settings.MAX_AGENTS)

        # ── Build AgentManifest ────────────────────────────────
        raw_agents = data.get("agents", [])
        # Validate each agent entry
        validated_agents = []
        seen_keys = set()
        for agent in raw_agents[:complexity.agent_count]:
            key = agent.get("key", "")
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            validated_agents.append({
                "key":   key,
                "name":  agent.get("name",  f"{key.capitalize()} Agent"),
                "tier":  int(agent.get("tier", 2)),
                "focus": agent.get("focus", state.query),
            })

        manifest = AgentManifest(
            agents=validated_agents,
            complexity=complexity,
            query_intent=data.get("query_intent", "general"),
            reasoning=data.get("reasoning", ""),
        )

        state.complexity     = complexity
        state.manifest       = manifest
        state.query_intent   = manifest.query_intent
        state.mark_phase_complete("planning")

        if settings.DEBUG_AGENTS:
            print(f"🧠 Orchestrator: {len(validated_agents)} agents, complexity {complexity.total:.1f}")
            print(f"   Intent: {manifest.query_intent}")

    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
        state.add_error("Orchestrator", "planning", str(e))
        # Fall back to a sensible default manifest
        state.manifest = _default_manifest(state.query)
        state.complexity = state.manifest.complexity

    return state


def _default_manifest(query: str) -> AgentManifest:
    """
    Fallback manifest used when the orchestrator LLM call fails.
    Runs a basic set of 6 core agents.
    """
    default_agents = [
        {"key": "trade",     "name": "Trade Agent",     "tier": 1, "focus": query},
        {"key": "finance",   "name": "Finance Agent",   "tier": 2, "focus": query},
        {"key": "labour",    "name": "Labour Agent",    "tier": 2, "focus": query},
        {"key": "inflation", "name": "Inflation Agent", "tier": 2, "focus": query},
        {"key": "energy",    "name": "Energy Agent",    "tier": 2, "focus": query},
        {"key": "geopolitics","name": "Geopolitics Agent","tier": 2,"focus": query},
    ]
    complexity = ComplexityScore(
        geographic_scope=2.5, domain_breadth=2.5, causal_depth=2.5,
        time_horizon=2.5, personal_relevance=2.5, total=2.5, agent_count=6,
    )
    return AgentManifest(
        agents=default_agents,
        complexity=complexity,
        query_intent="general",
        reasoning="Default manifest (orchestrator unavailable)",
    )
