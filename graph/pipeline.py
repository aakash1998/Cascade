"""
graph/pipeline.py — LangGraph StateGraph wiring all agents together
====================================================================
This is the central nervous system of Cascade. It defines the directed
graph of agent nodes and the conditional edges between them.

Architecture overview:
  State flows through as {"state": CascadeState}.
  Each node reads the state, does its work, and returns {"state": updated_state}.
  Conditional edges (routers) inspect the state and pick the next node.

Node execution order (happy path):
  orchestrate → scout → domain_agents → connector → watchdog
  → [debate] → historian → scenarios → personalise → summarise
  → log_predictions → END

Key design decisions:
  1. Domain agents run in parallel via asyncio.gather within one node —
     this is faster than LangGraph's Send API for our use case.

  2. Streaming events are emitted by putting progress into an asyncio.Queue
     that the /stream endpoint reads. Each major node emits events so the
     UI updates in real time.

  3. The graph is compiled once at module load and reused for all queries.
     State is always fresh (created per-query with create_initial_state()).

Usage:
  from graph.pipeline import run_pipeline, build_pipeline

  # Option A: Run and stream events
  async for event in run_pipeline(state, event_queue):
      pass  # events are emitted to event_queue as pipeline runs

  # Option B: Run to completion (no streaming)
  final_state = await build_pipeline().ainvoke({"state": state})
"""

import asyncio
from typing import Any, AsyncGenerator

from langgraph.graph import StateGraph, END

from config import settings
from graph.state import CascadeState, create_initial_state
from graph.routers import (
    route_after_orchestrator,  ORCHESTRATOR_ROUTES,
    route_after_scout,         SCOUT_ROUTES,
    route_after_domain_agents, DOMAIN_AGENTS_ROUTES,
    route_after_connector,     CONNECTOR_ROUTES,
    route_after_watchdog,      WATCHDOG_ROUTES,
    route_after_debate,        DEBATE_ROUTES,
    route_after_historian,     HISTORIAN_ROUTES,
    route_after_scenarios,     SCENARIO_ROUTES,
    route_after_personaliser,  PERSONALISER_ROUTES,
    route_after_summariser,    SUMMARISER_ROUTES,
)
from agents.orchestrator    import run_orchestrator
from agents.scout           import run_scout
from agents.connector       import run_connector
from agents.watchdog        import run_watchdog
from agents.debate_moderator import run_debate_moderator
from agents.historian       import run_historian
from agents.scenario_builder import run_scenario_builder
from agents.personaliser    import run_personaliser
from agents.summariser      import run_summariser
from agents.prediction_logger import run_prediction_logger
from agents.domain          import DOMAIN_REGISTRY


# ─────────────────────────────────────────────
# NODE WRAPPERS
# Each LangGraph node receives {"state": CascadeState}
# and must return {"state": updated_CascadeState}.
# ─────────────────────────────────────────────

async def _node_orchestrate(graph_state: dict) -> dict:
    """Plans the agent manifest and complexity score."""
    state = await run_orchestrator(graph_state["state"])
    return {"state": state}


async def _node_scout(graph_state: dict) -> dict:
    """Fetches real-time data from all APIs in parallel."""
    state = await run_scout(graph_state["state"])
    return {"state": state}


async def _node_domain_agents(graph_state: dict) -> dict:
    """
    Runs all selected domain agents in parallel using asyncio.gather.
    This is the heaviest node — can run 6-23 agents simultaneously.
    Each agent is given AGENT_TIMEOUT_SECONDS to complete.
    """
    state: CascadeState = graph_state["state"]
    manifest = state.manifest

    if settings.DEBUG_AGENTS:
        print(f"🚀 Running {len(manifest.agents)} domain agents in parallel...")

    # Build coroutines for all agents in the manifest
    coros = []
    agent_keys = []

    for agent_info in manifest.agents:
        key   = agent_info.get("key", "")
        agent = DOMAIN_REGISTRY.get(key)
        if agent is None:
            # Unknown domain key — skip gracefully
            if settings.DEBUG_AGENTS:
                print(f"⚠️  Unknown domain key: {key}")
            continue
        instance = agent()
        # Inject the focus from the manifest into the domain registry lookup
        coros.append(instance.run(state))
        agent_keys.append(agent_info.get("name", key))

    if not coros:
        return {"state": state}

    # Run all agents simultaneously — results come back in order
    results = await asyncio.gather(*coros, return_exceptions=True)

    for name, result in zip(agent_keys, results):
        if isinstance(result, Exception):
            print(f"⚠️  Agent {name} raised exception: {result}")
            state.failed_agents.append(name)
            continue
        if result is not None:
            state.agent_outputs[result.agent_name] = result

    state.mark_phase_complete("agents")

    if settings.DEBUG_AGENTS:
        completed = state.get_completed_agents()
        print(f"✅ Domain agents done: {len(completed)}/{len(coros)} succeeded")

    return {"state": state}


async def _node_connector(graph_state: dict) -> dict:
    """Builds the causal ripple chain from all agent outputs."""
    state = await run_connector(graph_state["state"])
    return {"state": state}


async def _node_watchdog(graph_state: dict) -> dict:
    """QA agent — flags low-confidence and contradictory claims."""
    state = await run_watchdog(graph_state["state"])
    return {"state": state}


async def _node_debate(graph_state: dict) -> dict:
    """Debate moderator — adjudicates conflicting agent views."""
    state = await run_debate_moderator(graph_state["state"])
    return {"state": state}


async def _node_historian(graph_state: dict) -> dict:
    """Finds historical parallels for the current event."""
    state = await run_historian(graph_state["state"])
    return {"state": state}


async def _node_scenarios(graph_state: dict) -> dict:
    """Builds best/base/worst case scenario branches."""
    state = await run_scenario_builder(graph_state["state"])
    return {"state": state}


async def _node_personalise(graph_state: dict) -> dict:
    """Personalises the analysis for the user's profile."""
    state = await run_personaliser(graph_state["state"])
    return {"state": state}


async def _node_summarise(graph_state: dict) -> dict:
    """Generates the final plain-language summary."""
    state = await run_summariser(graph_state["state"])
    return {"state": state}


async def _node_log_predictions(graph_state: dict) -> dict:
    """Logs verifiable predictions for future accuracy tracking."""
    state = await run_prediction_logger(graph_state["state"])

    # Mark pipeline complete
    from datetime import datetime, timezone
    state.completed_at = datetime.now(timezone.utc).isoformat()
    state.mark_phase_complete("complete")

    return {"state": state}


# ─────────────────────────────────────────────
# GRAPH BUILDER
# ─────────────────────────────────────────────

def build_pipeline():
    """
    Compiles and returns the LangGraph StateGraph.
    Call this once at startup — the compiled graph is reused for all queries.

    Returns a compiled LangGraph Runnable that accepts {"state": CascadeState}.
    """
    graph = StateGraph(dict)

    # ── Add nodes ──────────────────────────────────────────────
    graph.add_node("orchestrate",      _node_orchestrate)
    graph.add_node("scout",            _node_scout)
    graph.add_node("domain_agents",    _node_domain_agents)
    graph.add_node("connector",        _node_connector)
    graph.add_node("watchdog",         _node_watchdog)
    graph.add_node("debate",           _node_debate)
    graph.add_node("historian",        _node_historian)
    graph.add_node("scenarios",        _node_scenarios)
    graph.add_node("personalise",      _node_personalise)
    graph.add_node("summarise",        _node_summarise)
    graph.add_node("log_predictions",  _node_log_predictions)

    # ── Entry point ────────────────────────────────────────────
    graph.set_entry_point("orchestrate")

    # ── Conditional edges ──────────────────────────────────────
    graph.add_conditional_edges("orchestrate",   route_after_orchestrator,  ORCHESTRATOR_ROUTES)
    graph.add_conditional_edges("scout",         route_after_scout,         SCOUT_ROUTES)
    graph.add_conditional_edges("domain_agents", route_after_domain_agents, DOMAIN_AGENTS_ROUTES)
    graph.add_conditional_edges("connector",     route_after_connector,     CONNECTOR_ROUTES)
    graph.add_conditional_edges("watchdog",      route_after_watchdog,      WATCHDOG_ROUTES)
    graph.add_conditional_edges("debate",        route_after_debate,        DEBATE_ROUTES)
    graph.add_conditional_edges("historian",     route_after_historian,     HISTORIAN_ROUTES)
    graph.add_conditional_edges("scenarios",     route_after_scenarios,     SCENARIO_ROUTES)
    graph.add_conditional_edges("personalise",   route_after_personaliser,  PERSONALISER_ROUTES)
    graph.add_conditional_edges("summarise",     route_after_summariser,    SUMMARISER_ROUTES)

    # ── Terminal node ──────────────────────────────────────────
    graph.add_edge("log_predictions", END)

    return graph.compile()


# ─────────────────────────────────────────────
# STREAMING PIPELINE RUNNER
# ─────────────────────────────────────────────

async def run_pipeline_streaming(
    state:       CascadeState,
    event_queue: asyncio.Queue,
) -> CascadeState:
    """
    Runs the full pipeline and emits progress events into event_queue.
    Each major stage emits one or more events that the SSE endpoint reads.

    This is the function called by the /stream endpoint.

    Args:
        state:       Initial CascadeState (from create_initial_state)
        event_queue: asyncio.Queue — events are put() here as they happen

    Returns:
        The final CascadeState after all nodes complete.

    Events emitted (in order):
      {type: "status",       message: "..."}
      {type: "manifest",     complexity: {...}, agents: [...]}
      {type: "data_fetched", sources: [...]}
      {type: "agent_result", agent: "...", domain: "...", finding: "...", confidence: 0.x}
      {type: "chain_ready",  chain: [...]}
      {type: "chain_token",  token: "..."}      ← streaming narrative
      {type: "scenarios",    scenarios: [...]}
      {type: "personal_token", token: "..."}   ← streaming personal impact
      {type: "summary_token",  token: "..."}   ← streaming summary
      {type: "done",         run_id: "...", share_id: "..."}
      {type: "error",        message: "..."}
    """
    from streaming.sse import (
        make_status, make_manifest, make_data_fetched,
        make_agent_result, make_chain_ready, make_chain_token,
        make_scenarios, make_personal_token, make_summary_token,
        make_done, make_error,
    )

    async def emit(event: dict):
        await event_queue.put(event)
        await asyncio.sleep(0)  # yield to event loop so SSE can flush

    try:
        # ── Stage 1: Orchestrate ───────────────────────────────
        await emit(make_status("Analysing query complexity and planning agents..."))
        state = await run_orchestrator(state)

        if state.halt_pipeline:
            await emit(make_error(state.halt_reason or "Pipeline halted by orchestrator"))
            await emit({"type": "done", "cancelled": True})
            return state

        await emit(make_manifest(state))

        # ── Stage 2: Scout ─────────────────────────────────────
        await emit(make_status(f"Fetching real-time data from {6} sources..."))
        state = await run_scout(state)
        await emit(make_data_fetched(state))

        # ── Stage 3: Domain Agents ─────────────────────────────
        agent_count = len(state.manifest.agents)
        await emit(make_status(f"Running {agent_count} domain agents in parallel..."))

        # Run agents with per-agent event emission
        state = await _run_agents_with_events(state, emit, make_agent_result)

        if state.halt_pipeline:
            await emit(make_error("All domain agents failed"))
            await emit({"type": "done", "cancelled": True})
            return state

        # ── Stage 4: Connector ─────────────────────────────────
        await emit(make_status("Building causal ripple chain..."))
        state = await run_connector(state)
        await emit(make_chain_ready(state))

        # Stream the ripple chain narrative
        from agents.connector import stream_ripple_narrative
        async for token in stream_ripple_narrative(state):
            await emit(make_chain_token(token))

        # ── Stage 5: QA + Debate ───────────────────────────────
        await emit(make_status("Running quality assurance check..."))
        state = await run_watchdog(state)

        completed = state.get_completed_agents()
        if len(completed) >= 5 or len(state.hallucination_flags) >= 2:
            await emit(make_status("Running debate round to resolve conflicts..."))
            state = await run_debate_moderator(state)

        # ── Stage 6: History + Scenarios ──────────────────────
        await emit(make_status("Finding historical parallels..."))
        state = await run_historian(state)

        await emit(make_status("Building best/base/worst scenarios..."))
        state = await run_scenario_builder(state)
        await emit(make_scenarios(state))

        # ── Stage 7: Personalise ───────────────────────────────
        if not state.profile.is_empty():
            await emit(make_status("Personalising analysis for your profile..."))
        from agents.personaliser import stream_personal_impact
        async for token in stream_personal_impact(state):
            await emit(make_personal_token(token))
        # Save the streamed text to state
        state = await run_personaliser(state)

        # ── Stage 8: Final Summary ─────────────────────────────
        await emit(make_status("Writing final summary..."))
        from agents.summariser import stream_summary
        async for token in stream_summary(state):
            await emit(make_summary_token(token))
        state = await run_summariser(state)

        # ── Stage 9: Log Predictions ───────────────────────────
        state = await run_prediction_logger(state)

        # Done
        from datetime import datetime, timezone
        state.completed_at = datetime.now(timezone.utc).isoformat()
        state.mark_phase_complete("complete")
        await emit(make_done(state))

    except asyncio.CancelledError:
        # Client disconnected
        raise
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        await emit(make_error(str(e)))
        await emit({"type": "done", "cancelled": True, "error": str(e)})

    return state


async def _run_agents_with_events(
    state: CascadeState,
    emit,
    make_agent_result,
) -> CascadeState:
    """
    Runs domain agents in parallel and emits an event for each one as it completes.
    Uses asyncio.as_completed so events fire as soon as each agent finishes.
    """
    manifest = state.manifest

    # Build list of (agent_instance, agent_info) pairs
    agent_pairs = []
    for agent_info in manifest.agents:
        key     = agent_info.get("key", "")
        cls     = DOMAIN_REGISTRY.get(key)
        if cls is None:
            continue
        instance = cls()
        agent_pairs.append((instance, agent_info))

    if not agent_pairs:
        return state

    # Create tasks and map task → agent_info for event metadata
    loop = asyncio.get_event_loop()
    tasks = {
        asyncio.ensure_future(instance.run(state)): agent_info
        for instance, agent_info in agent_pairs
    }

    # Wait for tasks and emit events as each completes
    pending = set(tasks.keys())
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            agent_info = tasks[task]
            try:
                result = task.result()
                if result is not None:
                    state.agent_outputs[result.agent_name] = result
                    await emit(make_agent_result(result))
            except Exception as e:
                name = agent_info.get("name", "Unknown")
                print(f"⚠️  Agent {name} failed: {e}")
                state.failed_agents.append(name)

    state.mark_phase_complete("agents")
    return state


# ─────────────────────────────────────────────
# COMPILED PIPELINE SINGLETON
# ─────────────────────────────────────────────

# Build once at import time — reused for all queries
# Avoid building during tests if LangGraph is not installed
try:
    pipeline = build_pipeline()
except Exception as e:
    print(f"⚠️  Could not compile LangGraph pipeline: {e}")
    pipeline = None
