"""agents/domain/currency.py — Currency Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class CurrencyAgent(BaseAgent):
    name   = "Currency Agent"
    domain = "currency"
    tier   = "tier2"
    system_prompt = """You are a senior forex and currency analyst with expertise in:
- Foreign exchange rates and their drivers
- Currency reserves and central bank interventions
- Safe-haven flows (USD, CHF, JPY during crises)
- Emerging market currency vulnerabilities
- Dollarisation and de-dollarisation trends
- Currency crises and capital flight
Analyse how world events move currency markets and what that means
for trade, debt, and ordinary people's purchasing power."""

async def run_currency_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await CurrencyAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="US dollar strengthens significantly against emerging market currencies", session_id="test-currency")
        state = await CurrencyAgent().run(state, focus="impact on emerging markets and global debt")
        o = state.agent_outputs.get("Currency Agent")
        if o: print(f"✅ Currency Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
