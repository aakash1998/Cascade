"""agents/domain/labour.py — Labour Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class LabourAgent(BaseAgent):
    name   = "Labour Agent"
    domain = "labour"
    tier   = "tier2"
    system_prompt = """You are a senior labour economist with expertise in:
- Employment trends, layoffs, and hiring cycles
- Wage growth, real wages, and purchasing power
- Automation and AI displacement of jobs
- Sector-specific labour market dynamics
- Remote work, gig economy, and workforce shifts
- Union activity and collective bargaining
Analyse how world events ripple through labour markets.
Be specific about which job categories, sectors, and income groups are affected."""

async def run_labour_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await LabourAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Major AI companies announce 30% workforce reduction", session_id="test-labour")
        state = await LabourAgent().run(state, focus="tech sector employment impact")
        o = state.agent_outputs.get("Labour Agent")
        if o: print(f"✅ Labour Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
