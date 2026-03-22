"""agents/domain/climate.py — Climate Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class ClimateAgent(BaseAgent):
    name   = "Climate Agent"
    domain = "climate"
    tier   = "tier2"
    system_prompt = """You are a senior climate economist and environmental analyst with expertise in:
- Extreme weather events and their economic costs
- Carbon pricing, emissions trading, and climate policy
- Energy transition — solar, wind, battery storage economics
- Climate migration and displacement
- Agricultural impacts of climate change
- ESG investing trends and stranded asset risks
- International climate agreements and their implementation
Analyse how world events interact with climate systems, policy, and
the clean energy transition."""

async def run_climate_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await ClimateAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Record-breaking heatwave hits Southern Europe and North Africa", session_id="test-climate")
        state = await ClimateAgent().run(state, focus="economic and agricultural impact")
        o = state.agent_outputs.get("Climate Agent")
        if o: print(f"✅ Climate Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
