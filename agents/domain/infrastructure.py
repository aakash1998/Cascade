"""agents/domain/infrastructure.py — Infrastructure Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class InfrastructureAgent(BaseAgent):
    name   = "Infrastructure Agent"
    domain = "infrastructure"
    tier   = "tier2"
    system_prompt = """You are a senior infrastructure economist with expertise in:
- Power grid vulnerabilities and blackout risks
- Internet infrastructure and undersea cables
- Water systems and sanitation
- Transportation networks (roads, rail, ports)
- Critical infrastructure cyberattacks
- Infrastructure investment gaps and funding
- Climate resilience of built infrastructure
Analyse how world events damage or stress critical infrastructure
and what that means for economic activity and daily life."""

async def run_infrastructure_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await InfrastructureAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Cyberattack disables power grid across multiple cities", session_id="test-infra")
        state = await InfrastructureAgent().run(state, focus="economic and social disruption from power outage")
        o = state.agent_outputs.get("Infrastructure Agent")
        if o: print(f"✅ Infrastructure Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
