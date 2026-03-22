"""agents/domain/inflation.py — Inflation Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class InflationAgent(BaseAgent):
    name   = "Inflation Agent"
    domain = "inflation"
    tier   = "tier2"
    system_prompt = """You are a senior macroeconomist specialising in inflation with expertise in:
- Consumer price index (CPI) and its components
- Supply-side vs demand-side inflation drivers
- Central bank policy responses (rate hikes, QE/QT)
- Wage-price spirals and second-round effects
- Hyperinflation and currency debasement risks
- Purchasing power erosion across income groups
Analyse how world events drive inflation and erode purchasing power.
Be specific about which goods/services are affected and by how much."""

async def run_inflation_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await InflationAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Federal Reserve raises interest rates by 0.75%", session_id="test-inflation")
        state = await InflationAgent().run(state, focus="consumer price and purchasing power impact")
        o = state.agent_outputs.get("Inflation Agent")
        if o: print(f"✅ Inflation Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
