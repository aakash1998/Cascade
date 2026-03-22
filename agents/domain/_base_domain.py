"""
agents/domain/_base_domain.py — Shared base for all 23 domain agents
======================================================================
All domain agents inherit from DomainAgent, which handles:
  - Building the LLM prompt using the data context
  - Calling the LLM (tier2 by default = Groq free)
  - Parsing the structured JSON response
  - Populating the AgentOutput object

Each specific domain agent just needs to set:
  name            — display name
  domain          — domain key
  system_prompt   — expert persona for this domain
  tier            — "tier1" or "tier2" (default: "tier2")

The agent's 'focus' comes from the manifest at runtime —
so the same EnergyAgent can be used for "OPEC oil cuts" or
"renewable energy transition" depending on the query.
"""

import json
from typing import Optional

from agents.base_agent import BaseAgent
from llm.providers import call_llm
from graph.state import CascadeState, AgentOutput
from data.context_builder import build_agent_prompt
from config import settings


class DomainAgent(BaseAgent):
    """
    Base class for all 23 domain agents.

    Subclasses set:
      name:          str  — "Energy Agent"
      domain:        str  — "energy"
      system_prompt: str  — expert persona text
      tier:          str  — "tier1" | "tier2" (default tier2)

    No other code needed — _execute() handles everything.
    """

    # Subclasses override these
    name:          str = "Domain Agent"
    domain:        str = "domain"
    tier:          str = "tier2"
    system_prompt: str = "You are a domain expert analyst."

    async def _execute(self, state: CascadeState) -> AgentOutput:
        """
        Runs the domain analysis and returns a structured AgentOutput.
        Called by BaseAgent.run() with timeout + retry wrapping.
        """
        # Find this agent's specific focus from the manifest
        focus = self._get_focus(state)

        # Build the full prompt with data context embedded
        prompt = build_agent_prompt(
            query=state.query,
            domain=self.domain,
            focus=focus,
            data_context=state.data_context,
            profile_string=state.profile.to_prompt_string(),
            conversation_history=state.conversation_history,
        )

        # Call the LLM
        max_tokens = settings.MAX_TOKENS.get("domain_agent", 800)
        raw = await call_llm(
            prompt=prompt,
            tier=self.tier,
            max_tokens=max_tokens,
            system=self.system_prompt,
        )

        # Parse the structured JSON response
        data = self._parse_json_output(raw)

        # Build AgentOutput from the parsed data
        output = AgentOutput(
            agent_name=self.name,
            domain=self.domain,
            finding=            str(data.get("finding", "")),
            confidence=         self._safe_float(data.get("confidence", 0.5)),
            sources=            list(data.get("sources", [])),
            data_points=        list(data.get("data_points", [])),
            downstream_signals= list(data.get("downstream_signals", [])),
            timeframe=          str(data.get("timeframe", "unknown")),
            severity=           str(data.get("severity", "medium")),
            uncertainty_note=   str(data.get("uncertainty_note", "")),
            contradicting_view= str(data.get("contradicting_view", "")),
        )

        return output

    def _get_focus(self, state: CascadeState) -> str:
        """
        Finds this agent's focus from the Orchestrator's manifest.
        Falls back to the raw query if not found.
        """
        for agent_info in state.manifest.agents:
            if agent_info.get("key") == self.domain:
                return agent_info.get("focus", state.query)
        return state.query
