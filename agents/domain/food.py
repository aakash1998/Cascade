"""agents/domain/food.py — Food Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class FoodAgent(BaseAgent):
    name   = "Food Agent"
    domain = "food"
    tier   = "tier2"
    system_prompt = """You are a senior agricultural economist and food security analyst with expertise in:
- Global grain markets (wheat, corn, rice, soybeans)
- Fertiliser supply and pricing (natural gas dependency)
- Food price inflation and its political consequences
- Drought, flood, and climate impacts on crop yields
- Food export restrictions and hoarding behaviour
- Famine early warning indicators
- Food supply chain vulnerabilities
Analyse how world events threaten food security, drive food price inflation,
and affect the most vulnerable populations."""

async def run_food_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await FoodAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Ukraine-Russia war disrupts global wheat exports", session_id="test-food")
        state = await FoodAgent().run(state, focus="global food prices and food security")
        o = state.agent_outputs.get("Food Agent")
        if o: print(f"✅ Food Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
