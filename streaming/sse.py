"""
streaming/sse.py — SSE event builders for the Cascade pipeline
================================================================
This file contains factory functions for every SSE event type that
the pipeline emits to the frontend.

Why a dedicated module:
  Having all event shapes in one place makes it easy to:
  - See the full API contract at a glance
  - Change an event shape in one place (not scattered across agents)
  - Test event formatting independently of the pipeline

SSE protocol basics:
  Each event is a JSON string sent over an HTTP connection that stays open.
  The browser's EventSource API fires 'message' events for each one.
  Format: { "data": "<json string>" }

Event catalogue (what the frontend receives):
  status         — pipeline phase update ("Fetching data...")
  manifest       — agent plan + complexity score
  data_fetched   — which data sources responded
  agent_result   — one domain agent completed
  chain_ready    — full ripple chain structure
  chain_token    — one token of the chain narrative (streaming)
  scenarios      — three scenario branches
  personal_token — one token of the personal impact (streaming)
  summary_token  — one token of the final summary (streaming)
  done           — pipeline complete + share link
  error          — something went wrong

Usage:
  from streaming.sse import make_status, make_agent_result, make_done

  await event_queue.put(make_status("Analysing complexity..."))
  await event_queue.put(make_agent_result(output))
  await event_queue.put(make_done(state))
"""

import json
from typing import Any

from graph.state import CascadeState, AgentOutput


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _sse(payload: dict) -> dict:
    """
    Wraps a payload dict as an SSE event.
    The EventSourceResponse in main.py expects {"data": "<json string>"}.
    """
    return {"data": json.dumps(payload, default=str)}


# ─────────────────────────────────────────────
# EVENT BUILDERS
# ─────────────────────────────────────────────

def make_status(message: str, phase: str = "") -> dict:
    """
    Pipeline phase update — displayed in the UI status bar.

    Example:
      make_status("Running 12 domain agents in parallel...")
      → {"data": '{"type": "status", "message": "Running 12 domain agents..."}'}
    """
    return _sse({
        "type":    "status",
        "message": message,
        "phase":   phase,
    })


def make_manifest(state: CascadeState) -> dict:
    """
    Emitted after the Orchestrator completes.
    Tells the UI which agents are about to run and the complexity score.

    The UI uses this to draw the agent bubble grid.
    """
    complexity = state.complexity
    return _sse({
        "type": "manifest",
        "complexity": {
            "geographic_scope":   complexity.geographic_scope,
            "domain_breadth":     complexity.domain_breadth,
            "causal_depth":       complexity.causal_depth,
            "time_horizon":       complexity.time_horizon,
            "personal_relevance": complexity.personal_relevance,
            "total":              complexity.total,
            "agent_count":        complexity.agent_count,
            "display":            complexity.to_display_string(),
        },
        "agents": [
            {
                "key":   a.get("key", ""),
                "name":  a.get("name", ""),
                "tier":  a.get("tier", 2),
                "focus": a.get("focus", "")[:100],
            }
            for a in state.manifest.agents
        ],
        "query_intent": state.query_intent,
        "reasoning":    state.manifest.reasoning[:200] if state.manifest.reasoning else "",
    })


def make_data_fetched(state: CascadeState) -> dict:
    """
    Emitted after Scout completes.
    Tells the UI which data sources responded.
    """
    return _sse({
        "type":    "data_fetched",
        "sources": state.data_sources_used,
        "count":   len(state.data_sources_used),
        "fetched_at": state.data_fetched_at or "",
    })


def make_agent_result(output: AgentOutput) -> dict:
    """
    Emitted when one domain agent completes.
    The UI uses this to light up an agent bubble and show the finding.

    This event fires as soon as each agent finishes — not after all agents —
    so the UI updates live as results trickle in.
    """
    return _sse({
        "type":              "agent_result",
        "agent_name":        output.agent_name,
        "domain":            output.domain,
        "finding":           output.finding[:500],  # cap for SSE size
        "confidence":        round(output.confidence, 2),
        "sources":           output.sources[:5],
        "downstream":        output.downstream_signals[:5],
        "timeframe":         output.timeframe,
        "severity":          output.severity,
        "uncertainty_note":  output.uncertainty_note[:200],
        "status":            output.status,
    })


def make_agent_timeout(agent_name: str, domain: str) -> dict:
    """Emitted when a domain agent times out — the bubble turns grey in the UI."""
    return _sse({
        "type":       "agent_timeout",
        "agent_name": agent_name,
        "domain":     domain,
        "status":     "timeout",
    })


def make_chain_ready(state: CascadeState) -> dict:
    """
    Emitted after the Connector completes.
    Sends the full ripple chain structure so the UI can draw the graph.
    Also includes watchdog flags.
    """
    chain_data = [
        {
            "from_domain": link.from_domain,
            "to_domain":   link.to_domain,
            "mechanism":   link.mechanism[:200],
            "confidence":  round(link.confidence, 2),
            "timeframe":   link.timeframe,
            "tier":        link.tier,
        }
        for link in state.ripple_chain
    ]

    return _sse({
        "type":                "chain_ready",
        "ripple_chain":        chain_data,
        "link_count":          len(chain_data),
        "overall_confidence":  round(state.overall_confidence, 2),
        "hallucination_flags": state.hallucination_flags[:5],
    })


def make_chain_token(token: str) -> dict:
    """
    One streaming token from the ripple chain narrative.
    The UI appends these to the chain narrative text box in real time.
    """
    return _sse({"type": "chain_token", "token": token})


def make_scenarios(state: CascadeState) -> dict:
    """
    Emitted after the Scenario Builder completes.
    Contains all three scenario branches.
    """
    scenarios_data = [
        {
            "label":            s.label,
            "display_name":     s.display_name,
            "probability":      s.probability,
            "key_assumptions":  s.key_assumptions[:4],
            "ripple_summary":   s.ripple_summary[:300],
            "personal_impact":  s.personal_impact[:300],
        }
        for s in state.scenarios
    ]

    historical = []
    for p in state.historical_parallels[:2]:
        historical.append({
            "event":     p.get("event", ""),
            "year":      p.get("year", ""),
            "summary":   p.get("summary", "")[:200],
            "lesson":    p.get("lesson", "")[:150],
        })

    return _sse({
        "type":               "scenarios",
        "scenarios":          scenarios_data,
        "historical":         historical,
        "debate_conflicts":   state.debate_conflicts[:3],
        "debate_resolution":  state.debate_resolution[:300] if state.debate_resolution else "",
    })


def make_personal_token(token: str) -> dict:
    """One streaming token from the personalised impact narrative."""
    return _sse({"type": "personal_token", "token": token})


def make_summary_token(token: str) -> dict:
    """One streaming token from the final summary."""
    return _sse({"type": "summary_token", "token": token})


def make_done(state: CascadeState) -> dict:
    """
    Final event — pipeline complete.
    Contains metadata for the shareable link and accuracy tracking.
    """
    from data.cache import cache

    return _sse({
        "type":               "done",
        "run_id":             state.run_id,
        "share_id":           state.share_id,
        "completed_at":       state.completed_at or "",
        "agents_completed":   len(state.get_completed_agents()),
        "agents_failed":      len(state.failed_agents),
        "predictions_logged": len(state.predictions),
        "overall_confidence": round(state.overall_confidence, 2),
        "cost_usd":           round(state.estimated_cost_usd, 4),
        "error_count":        len(state.errors),
        "cache_stats":        cache.stats(),
    })


def make_error(message: str) -> dict:
    """Error event — shown as a toast notification in the UI."""
    return _sse({
        "type":    "error",
        "message": message[:300],
    })


def make_heartbeat() -> dict:
    """
    Periodic heartbeat to keep the SSE connection alive.
    Some proxies/load balancers close idle connections — this prevents that.
    Emitted every 15 seconds when the pipeline is running.
    """
    return _sse({"type": "heartbeat"})
