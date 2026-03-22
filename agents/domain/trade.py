"""agents/domain/trade.py — Trade Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class TradeAgent(BaseAgent):
    name   = "Trade Agent"
    domain = "trade"
    tier   = "tier2"
    system_prompt = """You are a senior international trade economist with expertise in:
- Tariff structures, trade wars, and WTO disputes
- Import/export flows and bilateral trade relationships
- Supply chain restructuring and nearshoring
- Trade sanctions and their secondary effects
- Free trade agreements and their labour/price impacts
Analyse how world events ripple through global trade flows.
Be specific about affected industries, countries, and price impacts."""

async def run_trade_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await TradeAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="US imposes 25% tariffs on all Chinese goods", session_id="test-trade")
        state = await TradeAgent().run(state, focus="impact on global trade flows")
        o = state.agent_outputs.get("Trade Agent")
        if o: print(f"✅ Trade Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
