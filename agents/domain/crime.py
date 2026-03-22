"""agents/domain/crime.py — Crime Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class CrimeAgent(BaseAgent):
    name   = "Crime Agent"
    domain = "crime"
    tier   = "tier2"
    system_prompt = """You are a senior criminologist and security analyst with expertise in:
- Crime rate trends during economic downturns
- Organised crime and its economic ecosystem
- Cybercrime and fraud escalation during crises
- Drug trafficking and addiction economics
- Political violence and state fragility
- Corruption and its drag on economic growth
- Policing capacity and justice system strain
Analyse how world events affect crime rates, security, and
the rule of law across different income groups."""

async def run_crime_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await CrimeAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Severe recession causes unemployment to spike to 20%", session_id="test-crime")
        state = await CrimeAgent().run(state, focus="crime rate and security impact")
        o = state.agent_outputs.get("Crime Agent")
        if o: print(f"✅ Crime Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
