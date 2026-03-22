"""
agents/orchestrator.py — Query analyser + agent planner
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
