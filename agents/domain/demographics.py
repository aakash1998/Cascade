"""agents/domain/demographics.py — Demographics Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class DemographicsAgent(BaseAgent):
    name   = "Demographics Agent"
    domain = "demographics"
    tier   = "tier2"
    system_prompt = """You are a senior demographer with expertise in:
- Population aging and pension system sustainability
- Birth rate decline and its economic consequences
- Generational wealth gaps (Boomers vs Millennials vs Gen Z)
- Workforce size projections and labour shortages
- Urbanisation and rural depopulation
- Life expectancy changes and healthcare costs
- Immigration as demographic buffer
Analyse how world events interact with demographic trends
to create long-term economic and social pressures."""

async def run_demographics_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await DemographicsAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Birth rates fall to record lows across developed world", session_id="test-demo")
        state = await DemographicsAgent().run(state, focus="economic and labour market consequences")
        o = state.agent_outputs.get("Demographics Agent")
        if o: print(f"✅ Demographics Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
