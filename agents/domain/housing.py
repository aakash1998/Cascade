"""agents/domain/housing.py — Housing Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class HousingAgent(BaseAgent):
    name   = "Housing Agent"
    domain = "housing"
    tier   = "tier2"
    system_prompt = """You are a senior real estate and housing market analyst with expertise in:
- Residential property prices and affordability
- Mortgage rates and their impact on demand
- Rental markets and landlord/tenant dynamics
- Construction costs and housing supply constraints
- Migration-driven demand shifts
- Housing market crashes and their economic contagion
- Government housing policy (rent controls, subsidies)
Analyse how world events affect housing affordability, mortgage costs,
and real estate markets across income groups."""

async def run_housing_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await HousingAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Interest rates rise to 6% as inflation persists", session_id="test-housing")
        state = await HousingAgent().run(state, focus="mortgage affordability and housing market impact")
        o = state.agent_outputs.get("Housing Agent")
        if o: print(f"✅ Housing Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
