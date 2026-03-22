"""
agents/domain/energy.py — Energy Domain Agent
===============================================
Analyses the impact of world events on energy markets:
oil prices, gas supply, electricity costs, renewables,
OPEC decisions, pipeline disruptions, energy policy.

This file is also the TEMPLATE for all other domain agents.
Every other agent follows this exact same pattern:
  1. Import BaseAgent
  2. Define name, domain, tier, system_prompt
  3. Optionally override build_prompt for custom logic
  4. That's it — BaseAgent handles everything else

To create a new domain agent, copy this file, change:
  - name
  - domain
  - system_prompt
  - The examples in build_prompt
  - The self-test query at the bottom

Current energy data sources used (injected by Scout):
  - FRED: crude oil prices, natural gas prices, energy CPI
  - Finnhub: energy sector stocks, commodity prices
  - Tavily: live news about OPEC, energy policy, supply disruptions
  - Open-Meteo: weather data (affects heating/cooling demand)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base_agent import BaseAgent
from graph.state import CascadeState


class EnergyAgent(BaseAgent):
    """
    Analyses energy market impacts of world events.

    Covers:
      - Crude oil and natural gas prices
      - OPEC production decisions
      - Pipeline and infrastructure disruptions
      - Electricity grid impacts
      - Renewables and energy transition
      - Energy sanctions and geopolitical supply risks
      - Consumer fuel and heating costs
    """

    name   = "Energy Agent"
    domain = "energy"
    tier   = "tier2"   # Groq — free, fast, excellent for domain analysis

    system_prompt = """You are a senior energy market analyst with expertise in:
- Global oil and gas markets (OPEC, shale, LNG)
- Energy geopolitics (pipeline politics, sanctions, supply routes)
- Electricity markets and grid stability
- Renewable energy transition and policy
- Consumer energy costs (fuel, heating, electricity)
- Energy security and strategic reserves

Your job is to analyse how a given world event ripples through energy markets.

Be specific about:
- Which energy prices are affected and by how much (give ranges)
- Which countries or regions feel this most acutely
- How quickly the impact hits (days vs months vs years)
- Which downstream sectors get hit next (transport, manufacturing, food)

Tone: Direct, analytical, grounded in data. No hype."""


    def build_prompt(self, state: CascadeState, focus: str = "") -> str:
        """
        Builds the energy-specific prompt.

        For most queries the default BaseAgent prompt works fine.
        This override adds energy-specific context cues to help
        the model give more targeted responses.
        """
        focus_line = f"\nSpecific focus: {focus}" if focus else ""

        energy_context = """
Key energy relationships to consider:
  - Oil supply shocks → inflation (transport, manufacturing, food)
  - Gas supply cuts → electricity prices → industrial output
  - OPEC production cuts → global oil price floor rises
  - Energy sanctions → alternative supply routes emerge (lag: 3-6 months)
  - Renewables insulate countries with high solar/wind penetration
  - Strategic reserves can buffer shocks for 60-90 days maximum
"""

        # Use parent's prompt builder for data context + profile injection
        base_prompt = super().build_prompt(state, focus)

        # Insert energy context after the main query line
        return f"{base_prompt}\n\n{energy_context}{focus_line}"


# ─────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────

async def run_energy_agent(state: CascadeState, focus: str = "") -> CascadeState:
    """
    Convenience wrapper — runs the Energy Agent on a state.
    Called by the pipeline when Energy Agent is in the manifest.

    Args:
        state: Current pipeline state
        focus: Specific aspect from orchestrator manifest

    Returns:
        Updated state with energy analysis in state.agent_outputs
    """
    agent = EnergyAgent()
    return await agent.run(state, focus)


# ─────────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test the Energy Agent directly:
      python -m agents.domain.energy
    """
    import asyncio
    from graph.state import create_initial_state

    async def test():
        print("\n🧪 Testing Energy Agent...\n")

        state = create_initial_state(
            query="Russia has cut gas supplies to Europe by 40%. What happens next?",
            session_id="test-energy-001",
            profile={
                "job":    "Factory worker",
                "city":   "Berlin, Germany",
                "sector": "Manufacturing",
            },
        )

        agent = EnergyAgent()
        print(f"Query: {state.query}")
        print(f"Running {agent.name}...\n")

        state = await agent.run(
            state,
            focus="immediate and medium-term impact on European energy prices and supply"
        )

        output = state.agent_outputs.get(agent.name)

        if output and output.status == "complete":
            print(f"✅ {agent.name} completed")
            print(f"\n   Confidence:  {output.confidence:.2f}")
            print(f"   Severity:    {output.severity}")
            print(f"   Timeframe:   {output.timeframe}")
            print(f"\n   Finding:")
            print(f"   {output.finding}")
            print(f"\n   Data points: {output.data_points}")
            print(f"   Downstream:  {output.downstream_signals}")
            print(f"   Uncertainty: {output.uncertainty_note}")
            print(f"\n   Counter-view:")
            print(f"   {output.contradicting_view}")
        else:
            print(f"❌ Agent failed")
            for err in state.errors:
                print(f"   Error: {err.message}")

        print("\n✅ Energy Agent test complete\n")

    asyncio.run(test())