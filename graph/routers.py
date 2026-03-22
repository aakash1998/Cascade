"""
graph/routers.py — Conditional edge routing logic for the LangGraph pipeline
=============================================================================
LangGraph uses router functions to decide which node to run next
based on the current state. Each router function:
  - Receives the current GraphState dict
  - Inspects the CascadeState inside it
  - Returns a string key that maps to the next node (or END)

Router inventory:
  route_after_orchestrator  — halt if content filter blocked query
  route_after_scout         — halt if no data fetched and dev mode off
  route_after_watchdog      — decide: needs_debate? → debate, else → historian
  route_after_connector     — always → watchdog (connector is never conditional)
  route_after_debate        — always → historian (debate always proceeds)

Pipeline flow diagram:
  START
    ↓
  [orchestrate]
    ↓ route_after_orchestrator
  [scout] ←──────────────────── returns "halt" → END
    ↓
  [domain_agents]
    ↓
  [connector]
    ↓
  [watchdog]
    ↓ route_after_watchdog
  ┌─── "needs_debate" → [debate]──┐
  └──────────────── "skip_debate" ─┘
    ↓
  [historian]
    ↓
  [scenarios]
    ↓
  [personalise]
    ↓
  [summarise]
    ↓
  [log_predictions]
    ↓
  END

Usage:
  from graph.routers import route_after_watchdog
  graph.add_conditional_edges("watchdog", route_after_watchdog, {...})
"""

from typing import Any

from graph.state import CascadeState


# ─────────────────────────────────────────────
# ROUTER FUNCTIONS
# Each receives the full GraphState dict and
# returns a routing key string.
# ─────────────────────────────────────────────

def route_after_orchestrator(graph_state: dict) -> str:
    """
    After Orchestrator: check if the query was halted (e.g. safety filter).

    Returns:
      "continue" → proceed to Scout (normal path)
      "halt"     → go directly to END (query blocked or critical error)
    """
    state: CascadeState = graph_state["state"]

    if state.halt_pipeline:
        return "halt"

    # Need at least one agent in the manifest to proceed
    if not state.manifest.agents:
        state.halt_pipeline = True
        state.halt_reason   = "Orchestrator returned empty agent manifest"
        return "halt"

    return "continue"


def route_after_scout(graph_state: dict) -> str:
    """
    After Scout: always continue — we run domain agents even if no data was fetched.
    (Agents will rely on their training knowledge when external data is absent.)

    Returns:
      "continue" → always
    """
    # Scout failures are soft — agents degrade gracefully without data
    return "continue"


def route_after_domain_agents(graph_state: dict) -> str:
    """
    After domain agents complete: check if any succeeded.

    Returns:
      "continue" → at least one agent completed (normal path)
      "halt"     → all agents failed (nothing to synthesise)
    """
    state: CascadeState = graph_state["state"]

    completed = state.get_completed_agents()
    if not completed:
        state.halt_pipeline = True
        state.halt_reason   = "All domain agents failed — no findings to synthesise"
        return "halt"

    return "continue"


def route_after_connector(graph_state: dict) -> str:
    """
    After Connector: always proceed to Watchdog.
    Even if the ripple chain is empty, Watchdog still QAs what we have.

    Returns:
      "continue" → always
    """
    return "continue"


def route_after_watchdog(graph_state: dict) -> str:
    """
    After Watchdog: decide whether to run the Debate Moderator.

    The Debate Moderator runs if:
      - There are at least 2 hallucination flags (suggests contradictions)
      - OR there are 5+ completed agents (enough for meaningful debate)
      - AND pipeline was not halted

    Returns:
      "needs_debate" → run Debate Moderator first
      "skip_debate"  → skip directly to Historian
      "halt"         → pipeline was halted during watchdog
    """
    state: CascadeState = graph_state["state"]

    if state.halt_pipeline:
        return "halt"

    completed = state.get_completed_agents()
    flag_count = len(state.hallucination_flags)

    # Debate is valuable when there are many agents or explicit flags
    if len(completed) >= 5 or flag_count >= 2:
        return "needs_debate"

    return "skip_debate"


def route_after_debate(graph_state: dict) -> str:
    """
    After Debate Moderator: always proceed to Historian.

    Returns:
      "continue" → always
    """
    return "continue"


def route_after_historian(graph_state: dict) -> str:
    """
    After Historian: always proceed to Scenarios.

    Returns:
      "continue" → always
    """
    return "continue"


def route_after_scenarios(graph_state: dict) -> str:
    """
    After Scenario Builder: always proceed to Personaliser.

    Returns:
      "continue" → always
    """
    return "continue"


def route_after_personaliser(graph_state: dict) -> str:
    """
    After Personaliser: always proceed to Summariser.

    Returns:
      "continue" → always
    """
    return "continue"


def route_after_summariser(graph_state: dict) -> str:
    """
    After Summariser: always proceed to Prediction Logger (final side effect).

    Returns:
      "continue" → always
    """
    return "continue"


# ─────────────────────────────────────────────
# ROUTING MAPS
# Used by graph.add_conditional_edges()
# Maps return value → next node name
# ─────────────────────────────────────────────

# After orchestrator
ORCHESTRATOR_ROUTES = {
    "continue": "scout",
    "halt":     "__end__",
}

# After scout
SCOUT_ROUTES = {
    "continue": "domain_agents",
}

# After domain agents
DOMAIN_AGENTS_ROUTES = {
    "continue": "connector",
    "halt":     "__end__",
}

# After connector
CONNECTOR_ROUTES = {
    "continue": "watchdog",
}

# After watchdog
WATCHDOG_ROUTES = {
    "needs_debate": "debate",
    "skip_debate":  "historian",
    "halt":         "__end__",
}

# After debate
DEBATE_ROUTES = {
    "continue": "historian",
}

# After historian
HISTORIAN_ROUTES = {
    "continue": "scenarios",
}

# After scenarios
SCENARIO_ROUTES = {
    "continue": "personalise",
}

# After personaliser
PERSONALISER_ROUTES = {
    "continue": "summarise",
}

# After summariser
SUMMARISER_ROUTES = {
    "continue": "log_predictions",
}
