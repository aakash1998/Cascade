"""agents/domain/geopolitics.py — Geopolitics Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class GeopoliticsAgent(BaseAgent):
    name   = "Geopolitics Agent"
    domain = "geopolitics"
    tier   = "tier2"
    system_prompt = """You are a senior geopolitical analyst with expertise in:
- Armed conflicts and their economic consequences
- Sanctions regimes and their effectiveness
- Alliance shifts (NATO, BRICS, bilateral agreements)
- Election outcomes and policy change risks
- Regime stability and political risk
- Diplomatic negotiations and their market impacts
Analyse how geopolitical events create economic and social ripple effects.
Be specific about affected regions, timelines, and escalation risks."""

async def run_geopolitics_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await GeopoliticsAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Conflict escalates in the Middle East", session_id="test-geo")
        state = await GeopoliticsAgent().run(state, focus="regional stability and global economic impact")
        o = state.agent_outputs.get("Geopolitics Agent")
        if o: print(f"✅ Geopolitics Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
