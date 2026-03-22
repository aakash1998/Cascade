"""
agents/base_agent.py — Base class for all domain agents
=========================================================
Every domain agent (Energy, Trade, Labour, etc.) inherits from
this class. It handles all the common logic so each domain agent
only needs to define:
  1. Its name and domain
  2. Its system prompt
  3. How to parse its specific output

What BaseAgent handles for every agent:
  - Calling the LLM with the right tier and token budget
  - Retry logic (up to AGENT_RETRY_BUDGET attempts)
  - Timeout handling (marks agent as timed out, pipeline continues)
  - Confidence scoring (self-reported by agent in structured output)
  - Hallucination check (flags outputs below confidence threshold)
  - Logging errors to state without crashing the pipeline
  - Injecting data context from Scout into the prompt
  - Injecting user profile into the prompt
  - Injecting conversation history for follow-up questions

How to create a new domain agent:
  class EnergyAgent(BaseAgent):
      name = "Energy Agent"
      domain = "energy"
      tier = "tier2"

      system_prompt = \"\"\"
      You are an expert energy market analyst.
      Analyse how the given world event affects:
      oil prices, gas supply, electricity costs, renewables.
      \"\"\"

      def build_prompt(self, state) -> str:
          return f"Analyse energy impacts of: {state.query}"

  # That's it. All retry, timeout, logging is handled by BaseAgent.

Usage:
  agent = EnergyAgent()
  updated_state = await agent.run(state)
  output = state.agent_outputs["Energy Agent"]
  print(output.finding)
  print(output.confidence)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from config import settings
from graph.state import CascadeState, AgentOutput
from llm.providers import call_llm_json


# ─────────────────────────────────────────────
# SHARED AGENT PROMPT TEMPLATES
# ─────────────────────────────────────────────
# These are injected into every domain agent's prompt
# so they all follow the same output format.

OUTPUT_FORMAT_INSTRUCTIONS = """
You must respond with ONLY a valid JSON object. No explanation, no markdown.

Required JSON structure:
{
  "finding": "<your main analysis — 2-4 sentences, plain English>",
  "confidence": <0.0 to 1.0 — how confident you are based on available data>,
  "sources": ["<source 1>", "<source 2>"],
  "data_points": ["<specific figure or fact>", "<another fact>"],
  "downstream_signals": ["<domain that will be affected next>"],
  "timeframe": "<when this ripple hits, e.g. '3-6 months'>",
  "severity": "<low|medium|high|critical>",
  "uncertainty_note": "<what would change this analysis>",
  "contradicting_view": "<the strongest argument against your finding>"
}

Confidence scoring guide:
  0.9+ = strong data support, clear causal link
  0.7-0.9 = good data support, likely outcome
  0.5-0.7 = limited data, uncertain outcome
  0.3-0.5 = weak data, speculative
  <0.3 = almost no data support — mark as highly uncertain

IMPORTANT rules:
  - Never use "will" or "definitely" — use "likely", "signals suggest", "may"
  - Base findings on the provided data context when available
  - If data is missing, lower your confidence score below 0.6
  - The contradicting_view must be a genuine counterargument, not a strawman
  - downstream_signals must be domain names from this list:
    Energy, Trade, Labour, Inflation, Geopolitics, Currency, Supply Chain,
    Technology, Housing, Healthcare, Climate, Food, Finance, Migration,
    Social, Mental Health, Education, Crime, Debt, Media, Demographics,
    Infrastructure, Culture
"""

DATA_CONTEXT_TEMPLATE = """
--- LIVE DATA CONTEXT ---
The following real data was fetched before you ran.
Base your analysis on this data where possible.
If a data source is empty, note this in your uncertainty_note.

{data_context}
--- END DATA CONTEXT ---
"""

PROFILE_TEMPLATE = """
--- USER PROFILE ---
Personalise your downstream_signals and timeframe for this user where relevant.
{profile}
--- END PROFILE ---
"""

HISTORY_TEMPLATE = """
--- CONVERSATION HISTORY ---
This is a follow-up question. Use this context.
{history}
--- END HISTORY ---
"""


# ─────────────────────────────────────────────
# BASE AGENT CLASS
# ─────────────────────────────────────────────

class BaseAgent:
    """
    Base class for all Cascade domain agents.

    Subclasses must define:
      name          (str)  — e.g. "Energy Agent"
      domain        (str)  — e.g. "energy"
      system_prompt (str)  — the agent's expertise and instructions
      build_prompt  (method) — returns the user prompt for this query

    Subclasses may override:
      tier          (str)  — "tier1" or "tier2" (default: "tier2")
      max_tokens    (int)  — override token budget (default: from config)
    """

    # ── Required — subclass must set these ────
    name:          str = "Base Agent"
    domain:        str = "base"
    system_prompt: str = "You are a helpful analyst."

    # ── Optional — subclass may override ──────
    tier:       str = "tier2"    # tier2 = Groq (free)
    max_tokens: int = 0          # 0 = use config default

    def _get_max_tokens(self) -> int:
        """Returns token budget for this agent."""
        if self.max_tokens > 0:
            return self.max_tokens
        return settings.MAX_TOKENS.get("domain_agent", 800)

    def build_prompt(self, state: CascadeState, focus: str = "") -> str:
        """
        Builds the user-facing prompt for this agent.
        Subclasses can override this for custom prompt logic.

        Default behaviour: combines query + data context + profile + history.
        The focus string comes from the orchestrator manifest — it tells
        this agent exactly what aspect to focus on for this query.
        """
        parts = []

        # Main task
        focus_text = f"\nFocus specifically on: {focus}" if focus else ""
        parts.append(
            f"Analyse the {self.domain} domain impact of the following query."
            f"{focus_text}\n\n"
            f"Query: {state.query}"
        )

        # Inject live data context if Scout has fetched data
        if state.data_context:
            # Only inject data relevant to this domain
            relevant_data = _extract_relevant_data(state.data_context, self.domain)
            if relevant_data:
                parts.append(DATA_CONTEXT_TEMPLATE.format(
                    data_context=json.dumps(relevant_data, indent=2)[:2000]
                ))

        # Inject user profile if available
        if not state.profile.is_empty():
            parts.append(PROFILE_TEMPLATE.format(
                profile=state.profile.to_prompt_string()
            ))

        # Inject conversation history for follow-up questions
        if len(state.conversation_history) > 1:
            # Include last 3 turns only — avoid prompt bloat
            recent = state.conversation_history[-3:]
            history_str = "\n".join([
                f"{turn.get('role', 'user').upper()}: {turn.get('content', '')[:200]}"
                for turn in recent
            ])
            parts.append(HISTORY_TEMPLATE.format(history=history_str))

        # Output format instructions — always last
        parts.append(OUTPUT_FORMAT_INSTRUCTIONS)

        return "\n\n".join(parts)

    def _build_system(self) -> str:
        """
        Combines the agent's domain system prompt with
        shared instructions for all agents.
        """
        return (
            f"{self.system_prompt}\n\n"
            "You are part of a multi-agent ripple effect analysis system. "
            "Your job is to analyse ONE specific domain deeply. "
            "Other agents are handling other domains in parallel. "
            "Be concise, grounded, and honest about uncertainty."
        )

    async def run(
        self,
        state:  CascadeState,
        focus:  str = "",
    ) -> CascadeState:
        """
        Runs this agent and writes its output to state.

        This is the main method called by the pipeline.
        It handles all retry, timeout, and error logic.

        Args:
            state: The current pipeline state (read + write)
            focus: Specific aspect to focus on (from orchestrator manifest)

        Returns:
            Updated state with this agent's output added to
            state.agent_outputs[self.name]
        """
        # Create the output object — starts as "pending"
        output = AgentOutput(
            agent_name=self.name,
            domain=self.domain,
            status="pending",
        )

        if settings.DEBUG_AGENTS:
            print(f"\n🔄 {self.name} starting... (focus: {focus[:40] if focus else 'none'})")

        # ── Retry loop ────────────────────────────────────────
        last_error = None
        for attempt in range(1, settings.AGENT_RETRY_BUDGET + 1):
            try:
                # Build prompts
                prompt = self.build_prompt(state, focus)
                system = self._build_system()

                # Call LLM with timeout
                raw = await asyncio.wait_for(
                    call_llm_json(
                        prompt=prompt,
                        system=system,
                        tier=self.tier,
                        max_tokens=self._get_max_tokens(),
                    ),
                    timeout=settings.AGENT_TIMEOUT_SECONDS,
                )

                # Parse the structured output
                output = _parse_agent_output(raw, self.name, self.domain)
                output.mark_complete()

                # ── Hallucination check ───────────────────────
                if output.confidence < settings.HALLUCINATION_CONFIDENCE_THRESHOLD:
                    if settings.DEBUG_AGENTS:
                        print(
                            f"   ⚠️  Low confidence ({output.confidence:.2f}) "
                            f"— flagging for watchdog"
                        )
                    state.hallucination_flags.append({
                        "agent":      self.name,
                        "confidence": output.confidence,
                        "flag":       "LOW_CONFIDENCE",
                        "finding":    output.finding[:100],
                    })

                if settings.DEBUG_AGENTS:
                    print(
                        f"   ✅ {self.name} done "
                        f"(confidence: {output.confidence:.2f}, "
                        f"attempt: {attempt})"
                    )

                break  # Success — exit retry loop

            except asyncio.TimeoutError:
                last_error = f"Timed out on attempt {attempt}"
                if settings.DEBUG_AGENTS:
                    print(f"   ⏱️  {self.name} timed out (attempt {attempt})")

                if attempt == settings.AGENT_RETRY_BUDGET:
                    output.mark_timeout()
                    state.failed_agents.append(self.name)

            except Exception as e:
                last_error = str(e)
                if settings.DEBUG_AGENTS:
                    print(f"   ❌ {self.name} error (attempt {attempt}): {e}")

                if attempt == settings.AGENT_RETRY_BUDGET:
                    output.mark_error(last_error)
                    state.failed_agents.append(self.name)
                    state.add_error(self.name, "agents", last_error)
                else:
                    # Wait briefly before retry
                    await asyncio.sleep(1)

        # Write output to state regardless of success/failure
        state.agent_outputs[self.name] = output
        return state


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _parse_agent_output(raw: dict, agent_name: str, domain: str) -> AgentOutput:
    """
    Parses the raw JSON dict from the LLM into an AgentOutput object.
    All fields have safe defaults so a partial response never crashes.
    """
    # Clamp confidence to 0.0-1.0
    confidence = float(raw.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    # Validate severity
    severity = raw.get("severity", "medium").lower()
    if severity not in ("low", "medium", "high", "critical"):
        severity = "medium"

    return AgentOutput(
        agent_name=agent_name,
        domain=domain,
        finding=raw.get("finding", "No finding returned"),
        confidence=confidence,
        sources=raw.get("sources", []),
        data_points=raw.get("data_points", []),
        downstream_signals=raw.get("downstream_signals", []),
        timeframe=raw.get("timeframe", "unknown"),
        severity=severity,
        uncertainty_note=raw.get("uncertainty_note", ""),
        contradicting_view=raw.get("contradicting_view", ""),
    )


def _extract_relevant_data(data_context: dict, domain: str) -> dict:
    """
    Extracts only the data sections relevant to a specific domain.
    Prevents agents from being distracted by irrelevant data.

    For example, the Energy Agent gets FRED oil price data
    but not the labour market job posting data.
    """
    # Domain → relevant data context keys
    domain_data_map = {
        "energy":       ["fred_energy", "commodities", "finnhub_energy", "tavily"],
        "trade":        ["fred_trade", "comtrade", "tariffs", "tavily"],
        "labour":       ["fred_labour", "bls", "layoffs", "tavily"],
        "inflation":    ["fred_inflation", "cpi", "interest_rates", "tavily"],
        "geopolitics":  ["gdelt", "acled", "tavily"],
        "currency":     ["fred_forex", "finnhub_forex", "tavily"],
        "supply_chain": ["shipping", "freight", "tavily"],
        "technology":   ["patents", "tavily", "finnhub_tech"],
        "housing":      ["fred_housing", "mortgage_rates", "tavily"],
        "finance":      ["fred_finance", "finnhub_markets", "tavily"],
        "climate":      ["weather", "climate", "tavily"],
        "food":         ["commodities", "agriculture", "tavily"],
        "social":       ["gdelt_social", "google_trends", "tavily"],
    }

    relevant_keys = domain_data_map.get(domain, ["tavily"])

    # Always include Tavily search results — most universally useful
    if "tavily" not in relevant_keys:
        relevant_keys.append("tavily")

    return {
        key: data_context[key]
        for key in relevant_keys
        if key in data_context
    }


# ─────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test the base agent with a minimal subclass:
      python -m agents.base_agent
    """
    import asyncio
    from graph.state import create_initial_state

    # Create a simple test agent using the base class
    class TestAgent(BaseAgent):
        name = "Test Agent"
        domain = "finance"
        tier = "tier2"
        system_prompt = (
            "You are a financial analyst specialising in market impacts. "
            "Analyse how world events affect financial markets and economies."
        )

    async def test():
        print("\n🧪 Testing BaseAgent...\n")

        state = create_initial_state(
            query="What does the US-China trade war mean for financial markets?",
            session_id="test-base-001",
            profile={"job": "Investor", "city": "Toronto"},
        )

        agent = TestAgent()

        print(f"Running {agent.name}...")
        state = await agent.run(state, focus="stock market and banking sector impacts")

        output = state.agent_outputs.get(agent.name)

        if output and output.status == "complete":
            print(f"\n✅ Agent completed successfully")
            print(f"   Status:      {output.status}")
            print(f"   Confidence:  {output.confidence:.2f}")
            print(f"   Severity:    {output.severity}")
            print(f"   Timeframe:   {output.timeframe}")
            print(f"   Finding:     {output.finding[:120]}...")
            print(f"   Downstream:  {output.downstream_signals}")
            print(f"   Sources:     {output.sources}")
            if output.contradicting_view:
                print(f"   Counter:     {output.contradicting_view[:80]}...")
        else:
            print(f"❌ Agent failed: {output.status if output else 'no output'}")
            print(f"   Errors: {state.errors}")

        print(f"\n   Hallucination flags: {len(state.hallucination_flags)}")
        print(f"   Failed agents:       {state.failed_agents}")
        print("\n✅ BaseAgent test complete\n")

    asyncio.run(test())