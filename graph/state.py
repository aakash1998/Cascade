"""
graph/state.py — Shared pipeline state
========================================
This is the single object that flows through every node in the
LangGraph pipeline. Think of it as a shared whiteboard that every
agent can read from and write to.

Why this matters:
  In LangGraph, agents don't talk to each other directly.
  Instead, each agent reads the current state, does its work,
  and writes its output back to the state. The next agent then
  reads the updated state.

  This means every agent always has full context of everything
  that happened before it — no agent ever starts blind.

What's in the state:
  - The user's query and profile
  - Which agents were spawned (the manifest)
  - Raw data fetched from APIs
  - Each agent's output as it completes
  - The ripple chain built by the Connector
  - Three scenario branches (best/base/worst)
  - The personalised impact for this user
  - Error log if anything went wrong
  - Metadata: run ID, timestamps, cost tracking

Usage:
  from graph.state import CascadeState, AgentOutput, create_initial_state

  # Create a fresh state for a new query
  state = create_initial_state(
      query="What does the US-China trade war mean for me?",
      session_id="abc-123",
      profile={"job": "engineer", "city": "Calgary"}
  )
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, field


# ─────────────────────────────────────────────
# SUB-OBJECTS
# These are the building blocks inside the state
# ─────────────────────────────────────────────

@dataclass
class UserProfile:
    """
    The user's onboarding answers.
    Used by the Personaliser to tailor the final analysis.
    All fields optional — user can skip any question.
    """
    job:            Optional[str] = None   # "Software engineer"
    city:           Optional[str] = None   # "Calgary, Canada"
    sector:         Optional[str] = None   # "Tech"
    household:      Optional[str] = None   # "Family with kids"
    housing:        Optional[str] = None   # "Own with mortgage"
    income_bracket: Optional[str] = None   # "$60k-$100k"
    extra_context:  Optional[str] = None   # "I have savings in USD"

    def to_prompt_string(self) -> str:
        """
        Converts the profile into a plain English string for agent prompts.
        Returns empty string if no profile was provided.

        Example output:
          "Job: Software engineer | City: Calgary, Canada |
           Sector: Tech | Household: Family with kids |
           Housing: Own with mortgage | Income: $60k-$100k |
           Extra: I have savings in USD"
        """
        parts = []
        if self.job:            parts.append(f"Job: {self.job}")
        if self.city:           parts.append(f"City: {self.city}")
        if self.sector:         parts.append(f"Sector: {self.sector}")
        if self.household:      parts.append(f"Household: {self.household}")
        if self.housing:        parts.append(f"Housing: {self.housing}")
        if self.income_bracket: parts.append(f"Income: {self.income_bracket}")
        if self.extra_context:  parts.append(f"Extra: {self.extra_context}")
        return " | ".join(parts) if parts else "No profile provided"

    def is_empty(self) -> bool:
        """Returns True if the user skipped all onboarding questions."""
        return all(v is None for v in [
            self.job, self.city, self.sector,
            self.household, self.housing,
            self.income_bracket, self.extra_context
        ])


@dataclass
class ComplexityScore:
    """
    The 5-dimensional complexity score calculated by the Orchestrator.
    Each dimension is scored 1.0-5.0. The weighted total decides
    how many agents to spin up.

    Dimensions:
      geographic_scope  — how many countries/regions affected
      domain_breadth    — how many sectors are touched
      causal_depth      — how many steps removed is the final impact
      time_horizon      — days vs months vs years
      personal_relevance — how directly the user profile is affected
    """
    geographic_scope:   float = 1.0
    domain_breadth:     float = 1.0
    causal_depth:       float = 1.0
    time_horizon:       float = 1.0
    personal_relevance: float = 1.0
    total:              float = 1.0
    agent_count:        int   = 8    # total agents to spawn

    def to_display_string(self) -> str:
        """Human-readable version shown in the UI."""
        return (
            f"Geographic: {self.geographic_scope:.1f} | "
            f"Domains: {self.domain_breadth:.1f} | "
            f"Depth: {self.causal_depth:.1f} | "
            f"Time: {self.time_horizon:.1f} | "
            f"Personal: {self.personal_relevance:.1f} | "
            f"Total: {self.total:.1f} → {self.agent_count} agents"
        )


@dataclass
class AgentManifest:
    """
    The list of agents to spawn, created by the Orchestrator.
    Each entry tells us: which agent, which tier, what to focus on.

    Example:
      agents = [
        AgentTask(name="Energy Agent",   tier=1, focus="OPEC production cuts"),
        AgentTask(name="Labour Agent",   tier=2, focus="tech job market Canada"),
        AgentTask(name="Inflation Agent",tier=2, focus="consumer price impact"),
      ]
    """
    agents:          list  = field(default_factory=list)
    complexity:      ComplexityScore = field(default_factory=ComplexityScore)
    query_intent:    str   = "general"    # personal_impact, prediction, causal_chain, etc.
    reasoning:       str   = ""           # why the orchestrator chose these agents


@dataclass
class AgentOutput:
    """
    The structured output from one domain agent.
    Every domain agent returns exactly this structure.

    confidence: 0.0-1.0 — how sure the agent is
    sources: which APIs/data backed this finding
    downstream_signals: which other domains this affects next
    timeframe: when this ripple hits (e.g. "3-6 months")
    severity: low / medium / high / critical
    contradicting_view: the other side of the argument
    """
    agent_name:          str   = ""
    domain:              str   = ""
    finding:             str   = ""          # main analysis text
    confidence:          float = 0.5
    sources:             list  = field(default_factory=list)
    data_points:         list  = field(default_factory=list)
    downstream_signals:  list  = field(default_factory=list)
    timeframe:           str   = "unknown"
    severity:            str   = "medium"
    uncertainty_note:    str   = ""
    contradicting_view:  str   = ""
    status:              str   = "pending"   # pending / complete / timeout / error
    completed_at:        Optional[str] = None

    def mark_complete(self):
        """Call this when the agent finishes successfully."""
        self.status = "complete"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_timeout(self):
        """Call this when the agent exceeds AGENT_TIMEOUT_SECONDS."""
        self.status = "timeout"
        self.finding = "Agent timed out — result not available"
        self.confidence = 0.0
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_error(self, error: str):
        """Call this when the agent hits an unexpected error."""
        self.status = "error"
        self.finding = f"Agent error: {error}"
        self.confidence = 0.0
        self.completed_at = datetime.now(timezone.utc).isoformat()


@dataclass
class RippleLink:
    """
    One connection in the ripple chain.
    Represents: Domain A causes Effect B with Confidence C.

    Example:
      RippleLink(
        from_domain="Trade",
        to_domain="Labour",
        mechanism="Tariffs slow exports → fewer manufacturing jobs",
        confidence=0.74,
        timeframe="3-6 months",
        tier=2
      )
    """
    from_domain: str   = ""
    to_domain:   str   = ""
    mechanism:   str   = ""     # plain English explanation of the link
    confidence:  float = 0.5
    timeframe:   str   = ""
    tier:        int   = 1      # 1=direct, 2=indirect, 3=distant


@dataclass
class ScenarioBranch:
    """
    One of three scenario branches (best / base / worst).
    Each branch contains a modified ripple chain showing what
    happens under different assumptions.
    """
    label:           str  = ""    # "best_case" | "base_case" | "worst_case"
    display_name:    str  = ""    # "Best case" | "Base case" | "Worst case"
    key_assumptions: list = field(default_factory=list)
    ripple_summary:  str  = ""    # plain English summary of this scenario
    personal_impact: str  = ""    # how this scenario affects this user
    probability:     str  = ""    # "Low" | "Medium" | "High"


@dataclass
class PredictionEntry:
    """
    A single verifiable claim logged for future accuracy tracking.
    The verifier job checks these 30 and 90 days after they are made.

    This is the feedback loop — the feature that turns Cascade
    from a demo into a credible system over time.
    """
    id:               str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    claim:            str   = ""      # "Canadian tech hiring will slow 10-15%"
    domain:           str   = ""      # "labour"
    direction:        str   = ""      # "decrease" | "increase" | "stable"
    timeframe_days:   int   = 90
    confidence:       float = 0.5
    generated_at:     str   = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verification_date:str   = ""      # generated_at + timeframe_days
    status:           str   = "pending"  # pending / correct / incorrect / partial
    actual_outcome:   str   = ""


@dataclass
class ErrorEntry:
    """
    Records any error that happened during the pipeline run.
    Stored in the state so the frontend can show what went wrong.
    """
    agent:     str = ""
    phase:     str = ""
    message:   str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────
# MAIN STATE OBJECT
# ─────────────────────────────────────────────

@dataclass
class CascadeState:
    """
    The complete shared state for one pipeline run.

    This object is created when a query comes in and passed
    through every node in the LangGraph pipeline.

    Each node reads what it needs and writes its output back.
    The state grows richer as it moves through the pipeline.

    Sections:
      Identity    — run ID, session, timestamps
      Input       — the query, profile, conversation history
      Planning    — complexity score, agent manifest
      Data        — fetched from APIs by Scout
      Agent work  — outputs from each domain agent
      Synthesis   — ripple chain, scenarios, counterfactuals
      Output      — final personalised analysis and summary
      Trust       — citations, hallucination flags, predictions
      Control     — pipeline phase, errors, flags
    """

    # ── IDENTITY ──────────────────────────────
    # Unique ID for this run — used in shareable links and logs
    run_id:     str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    session_id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    # ── INPUT ─────────────────────────────────
    # The raw query from the user
    query: str = ""

    # The user's profile from onboarding
    profile: UserProfile = field(default_factory=UserProfile)

    # Full conversation history for this session
    # Enables follow-up questions to work correctly
    conversation_history: list = field(default_factory=list)

    # ── PLANNING ──────────────────────────────
    # Set by the Orchestrator after reading the query
    complexity:       ComplexityScore = field(default_factory=ComplexityScore)
    manifest:         AgentManifest   = field(default_factory=AgentManifest)
    query_intent:     str = "general"

    # ── DATA CONTEXT ──────────────────────────
    # Raw data fetched by Scout from all APIs
    # Passed to every domain agent as grounding context
    # Structure: { "fred": {...}, "gdelt": [...], "tavily": [...], ... }
    data_context: dict = field(default_factory=dict)

    # Which data sources successfully responded
    data_sources_used: list = field(default_factory=list)

    # When the data was fetched (for staleness warnings)
    data_fetched_at: Optional[str] = None

    # ── AGENT OUTPUTS ─────────────────────────
    # Results from each domain agent, keyed by agent name
    # e.g. { "Energy Agent": AgentOutput(...), "Labour Agent": AgentOutput(...) }
    agent_outputs: dict = field(default_factory=dict)

    # Agents that timed out or errored — shown in UI as greyed out
    failed_agents: list = field(default_factory=list)

    # ── SYNTHESIS ─────────────────────────────
    # The ripple chain — list of RippleLink objects
    # Built by the Connector from all agent outputs
    ripple_chain: list = field(default_factory=list)

    # Conflicts found during the debate round
    # e.g. [{"agents": ["Labour", "Finance"], "conflict": "..."}]
    debate_conflicts: list = field(default_factory=list)
    debate_resolution: str = ""

    # Historical events similar to this query
    # Found by the Historian agent
    historical_parallels: list = field(default_factory=list)

    # Three scenario branches
    scenarios: list = field(default_factory=list)  # List of ScenarioBranch

    # What-if analysis from the Counterfactual agent
    counterfactuals: list = field(default_factory=list)

    # ── OUTPUT ────────────────────────────────
    # The personalised impact statement from the Personaliser
    personal_impact: str = ""

    # Final plain-language summary from the Summariser
    summary: str = ""

    # Unique ID for the shareable link
    share_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])

    # ── TRUST ─────────────────────────────────
    # Hallucination flags raised by the Watchdog
    # e.g. [{"agent": "Energy", "claim": "...", "flag": "UNSUPPORTED"}]
    hallucination_flags: list = field(default_factory=list)

    # Predictions logged for future verification
    predictions: list = field(default_factory=list)  # List of PredictionEntry

    # Overall confidence score for the full analysis (0.0-1.0)
    overall_confidence: float = 0.0

    # ── CONTROL ───────────────────────────────
    # Current pipeline phase — used for checkpoint/resume
    # Values: init → planning → fetching → agents → synthesis
    #         → trust → output → complete → error
    current_phase: str = "init"

    # Which phases have completed — for checkpoint/resume after crash
    completed_phases: list = field(default_factory=list)

    # Error log — non-fatal errors that happened during the run
    errors: list = field(default_factory=list)  # List of ErrorEntry

    # Set to True to halt the pipeline immediately
    # Used by watchdog if something critical is detected
    halt_pipeline: bool = False
    halt_reason:   str  = ""

    # ── COST TRACKING ─────────────────────────
    # Approximate cost of this run in USD
    estimated_cost_usd: float = 0.0

    # ── METHODS ───────────────────────────────

    def add_error(self, agent: str, phase: str, message: str):
        """Logs a non-fatal error to the error list."""
        self.errors.append(ErrorEntry(
            agent=agent,
            phase=phase,
            message=message,
        ))

    def mark_phase_complete(self, phase: str):
        """Records that a pipeline phase finished successfully."""
        if phase not in self.completed_phases:
            self.completed_phases.append(phase)
        self.current_phase = phase

    def is_phase_complete(self, phase: str) -> bool:
        """Used by checkpoint system to skip already-completed phases."""
        return phase in self.completed_phases

    def get_agent_output(self, agent_name: str) -> Optional[AgentOutput]:
        """Returns the output for a specific agent, or None if not complete."""
        return self.agent_outputs.get(agent_name)

    def get_completed_agents(self) -> list:
        """Returns list of agent names that completed successfully."""
        return [
            name for name, output in self.agent_outputs.items()
            if output.status == "complete"
        ]

    def get_high_confidence_findings(self, threshold: float = 0.7) -> list:
        """
        Returns agent outputs with confidence above threshold.
        Used by the Connector to prioritise strong signals.
        """
        return [
            output for output in self.agent_outputs.values()
            if output.confidence >= threshold and output.status == "complete"
        ]

    def to_summary_dict(self) -> dict:
        """
        Returns a lightweight summary of the state.
        Used for the /health endpoint and debug logging.
        """
        return {
            "run_id":             self.run_id,
            "session_id":         self.session_id,
            "query":              self.query[:80] + "..." if len(self.query) > 80 else self.query,
            "phase":              self.current_phase,
            "agents_complete":    len(self.get_completed_agents()),
            "agents_failed":      len(self.failed_agents),
            "ripple_links":       len(self.ripple_chain),
            "predictions_logged": len(self.predictions),
            "errors":             len(self.errors),
            "cost_usd":           round(self.estimated_cost_usd, 4),
            "confidence":         round(self.overall_confidence, 2),
        }


# ─────────────────────────────────────────────
# FACTORY FUNCTION
# ─────────────────────────────────────────────

def create_initial_state(
    query:      str,
    session_id: str = "",
    profile:    dict = None,
    history:    list = None,
) -> CascadeState:
    """
    Creates a fresh CascadeState for a new query.
    This is the only place state objects should be created.

    Args:
        query:      The user's question
        session_id: The session UUID from the browser
        profile:    Dict of onboarding answers (can be empty)
        history:    Previous conversation turns (can be empty)

    Returns:
        A clean CascadeState ready to enter the pipeline

    Example:
        state = create_initial_state(
            query="What does the Russia-Ukraine war mean for energy prices?",
            session_id="abc-123",
            profile={"job": "Teacher", "city": "Toronto", "sector": "Education"},
        )
    """
    # Build UserProfile from dict
    user_profile = UserProfile()
    if profile:
        user_profile.job            = profile.get("job")
        user_profile.city           = profile.get("city")
        user_profile.sector         = profile.get("sector")
        user_profile.household      = profile.get("household")
        user_profile.housing        = profile.get("housing")
        user_profile.income_bracket = profile.get("income_bracket")
        user_profile.extra_context  = profile.get("extra_context")

    return CascadeState(
        query=query.strip(),
        session_id=session_id,
        profile=user_profile,
        conversation_history=history or [],
        current_phase="init",
    )


# ─────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test that the state objects work correctly:
      python -m graph.state
    """
    print("\n🧪 Testing CascadeState...\n")

    # Create a state
    state = create_initial_state(
        query="What does the US-China trade war mean for a software engineer in Calgary?",
        session_id="test-session-001",
        profile={
            "job":    "Software engineer",
            "city":   "Calgary, Canada",
            "sector": "Tech",
            "household": "Family with kids",
            "housing":   "Own with mortgage",
        },
    )

    print(f"✅ State created")
    print(f"   Run ID:     {state.run_id}")
    print(f"   Query:      {state.query[:60]}...")
    print(f"   Profile:    {state.profile.to_prompt_string()}")
    print(f"   Phase:      {state.current_phase}")

    # Test agent output
    output = AgentOutput(
        agent_name="Energy Agent",
        domain="energy",
        finding="Oil prices will rise 15% within 3 months due to supply disruptions.",
        confidence=0.82,
        sources=["FRED", "Finnhub"],
        downstream_signals=["Inflation", "Trade"],
        timeframe="3 months",
        severity="high",
    )
    output.mark_complete()
    state.agent_outputs["Energy Agent"] = output
    state.mark_phase_complete("agents")

    print(f"\n✅ Agent output added")
    print(f"   Agent:      {output.agent_name}")
    print(f"   Confidence: {output.confidence}")
    print(f"   Status:     {output.status}")
    print(f"   Downstream: {output.downstream_signals}")

    # Test ripple link
    link = RippleLink(
        from_domain="Energy",
        to_domain="Inflation",
        mechanism="Higher oil prices increase transportation and manufacturing costs",
        confidence=0.78,
        timeframe="2-4 months",
        tier=2,
    )
    state.ripple_chain.append(link)

    print(f"\n✅ Ripple link added")
    print(f"   {link.from_domain} → {link.to_domain}")
    print(f"   Mechanism: {link.mechanism[:50]}...")

    # Test summary
    print(f"\n📊 State summary:")
    summary = state.to_summary_dict()
    for k, v in summary.items():
        print(f"   {k}: {v}")

    print("\n✅ All state tests passed\n")