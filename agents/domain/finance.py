"""agents/domain/finance.py — Finance Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class FinanceAgent(BaseAgent):
    name   = "Finance Agent"
    domain = "finance"
    tier   = "tier2"
    system_prompt = """You are a senior financial markets analyst with expertise in:
- Stock market volatility and sector rotations
- Banking sector stability and credit risk
- Sovereign debt and government borrowing costs
- Private equity and venture capital cycles
- Recession indicators and GDP forecasting
- Financial contagion and systemic risk
- Commodity markets (gold, silver, copper as signals)
Analyse how world events move financial markets, affect credit availability,
and signal recession or recovery."""

async def run_finance_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await FinanceAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Global stock markets drop 15% in one week", session_id="test-finance")
        state = await FinanceAgent().run(state, focus="market contagion and recession risk")
        o = state.agent_outputs.get("Finance Agent")
        if o: print(f"✅ Finance Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
