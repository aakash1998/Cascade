"""agents/domain/debt.py — Debt Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class DebtAgent(BaseAgent):
    name   = "Debt Agent"
    domain = "debt"
    tier   = "tier2"
    system_prompt = """You are a senior debt and credit analyst with expertise in:
- Household debt levels and debt service ratios
- Credit card, mortgage, and student loan delinquencies
- Personal bankruptcy trends and triggers
- Sovereign debt sustainability and default risk
- Corporate debt and leveraged buyout risks
- Credit rating agency actions and their consequences
- Debt restructuring and its social impact
Analyse how world events strain household and sovereign debt,
tighten credit, and push borrowers toward default."""

async def run_debt_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await DebtAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Interest rates rise sharply — mortgages become unaffordable", session_id="test-debt")
        state = await DebtAgent().run(state, focus="household debt stress and default risk")
        o = state.agent_outputs.get("Debt Agent")
        if o: print(f"✅ Debt Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
