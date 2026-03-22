"""
agents/base_agent.py — Abstract base class for all Cascade agents
==================================================================
Every agent in the system (domain agents, orchestrator, connector,
summariser, etc.) inherits from BaseAgent.

What this provides:
  - Consistent interface: every agent has a run() method
  - Shared error handling with automatic retries
  - Timeout enforcement (AGENT_TIMEOUT_SECONDS)
  - Structured logging for every agent call
  - Cost tracking hooks

How to create a new agent:
  class EnergyAgent(BaseAgent):
      name   = "Energy Agent"
      domain = "energy"
      tier   = "tier2"        # tier1 = Claude, tier2 = Groq (free)

      async def _execute(self, state: CascadeState) -> AgentOutput:
          prompt = build_agent_prompt(state.query, self.domain, ...)
          raw    = await call_llm(prompt, tier=self.tier, ...)
          data   = json.loads(raw)
          return AgentOutput(
              agent_name=self.name,
              domain=self.domain,
              finding=data["finding"],
              confidence=data["confidence"],
              ...
          )
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from config import settings
from graph.state import CascadeState, AgentOutput


class BaseAgent(ABC):
    """
    Abstract base class for all Cascade agents.

    Subclasses must define:
      - name:   str — display name (e.g. "Energy Agent")
      - domain: str — domain key (e.g. "energy")
      - tier:   str — "tier1" (Claude) or "tier2" (Groq free)

    Subclasses must implement:
      - _execute(state) -> AgentOutput

    The run() method wraps _execute() with timeout + error handling.
    """

    name:   str = "BaseAgent"
    domain: str = "base"
    tier:   str = "tier2"

    def __init__(self):
        # Each agent can override these defaults
        self.max_tokens = settings.MAX_TOKENS.get(self.domain, 800)
        self.timeout    = settings.AGENT_TIMEOUT_SECONDS
        self.retries    = settings.AGENT_RETRY_BUDGET

    @abstractmethod
    async def _execute(self, state: CascadeState) -> AgentOutput:
        """
        Core agent logic. Subclasses implement this.
        Should return a fully populated AgentOutput.
        Should raise exceptions on failure — run() handles them.
        """
        ...

    async def run(self, state: CascadeState) -> AgentOutput:
        """
        Runs the agent with timeout and retry logic.
        This is the method the pipeline calls.

        Returns an AgentOutput that is always fully populated —
        even on error or timeout (with status="error"/"timeout").
        """
        output = AgentOutput(
            agent_name=self.name,
            domain=self.domain,
        )

        last_error = ""

        for attempt in range(self.retries):
            try:
                if settings.DEBUG_AGENTS:
                    print(f"🤖 {self.name} starting (attempt {attempt + 1}/{self.retries})")

                # Enforce timeout on the whole _execute() call
                result = await asyncio.wait_for(
                    self._execute(state),
                    timeout=self.timeout,
                )

                result.mark_complete()

                if settings.DEBUG_AGENTS:
                    print(f"✅ {self.name} done — confidence: {result.confidence:.2f}")

                return result

            except asyncio.TimeoutError:
                last_error = f"Timed out after {self.timeout}s"
                print(f"⏱️  {self.name} timed out (attempt {attempt + 1})")
                if attempt < self.retries - 1:
                    await asyncio.sleep(0.5)
                continue

            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                print(f"⚠️  {self.name} JSON error (attempt {attempt + 1}): {e}")
                if attempt < self.retries - 1:
                    await asyncio.sleep(0.5)
                continue

            except Exception as e:
                last_error = str(e)
                print(f"⚠️  {self.name} error (attempt {attempt + 1}): {e}")
                if attempt < self.retries - 1:
                    await asyncio.sleep(0.5)
                continue

        # All retries exhausted
        if "timed out" in last_error.lower():
            output.mark_timeout()
        else:
            output.mark_error(last_error)

        state.failed_agents.append(self.name)
        state.add_error(self.name, "execution", last_error)
        return output

    def _parse_json_output(self, raw: str) -> dict:
        """
        Parses LLM JSON output, stripping markdown code fences if present.
        Used by domain agents to parse structured responses.
        Raises json.JSONDecodeError if parsing fails.
        """
        cleaned = raw.strip()
        # Strip ```json ... ``` or ``` ... ```
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()
        return json.loads(cleaned)

    def _safe_float(self, value, default: float = 0.5) -> float:
        """Safely converts a value to float, returning default on failure."""
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return default

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, domain={self.domain!r}, tier={self.tier!r})"
