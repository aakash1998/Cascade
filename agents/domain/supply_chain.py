"""agents/domain/supply_chain.py — Supply Chain Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class SupplyChainAgent(BaseAgent):
    name   = "Supply Chain Agent"
    domain = "supply_chain"
    tier   = "tier2"
    system_prompt = """You are a senior supply chain and logistics expert with expertise in:
- Global shipping routes and freight rates
- Port congestion and logistics bottlenecks
- Just-in-time vs resilient supply chain models
- Semiconductor and critical component shortages
- Nearshoring, friendshoring, and reshoring trends
- Raw material sourcing and commodity dependencies
Analyse how world events disrupt supply chains and what cascades downstream
into manufacturing, retail, and consumer prices."""

async def run_supply_chain_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await SupplyChainAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Major ports in Asia shut down due to conflict", session_id="test-supply")
        state = await SupplyChainAgent().run(state, focus="shipping disruption and manufacturing impact")
        o = state.agent_outputs.get("Supply Chain Agent")
        if o: print(f"✅ Supply Chain Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
