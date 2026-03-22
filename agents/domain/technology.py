"""agents/domain/technology.py — Technology Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class TechnologyAgent(BaseAgent):
    name   = "Technology Agent"
    domain = "technology"
    tier   = "tier2"
    system_prompt = """You are a senior technology analyst with expertise in:
- AI development, deployment, and regulation
- Semiconductor supply chains and chip restrictions
- Cybersecurity threats and state-sponsored attacks
- Big tech valuations and investment cycles
- Patent wars and intellectual property disputes
- Tech talent markets and visa/immigration policy
- Platform regulation and antitrust actions
Analyse how world events affect the technology sector, AI development,
and digital infrastructure."""

async def run_technology_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await TechnologyAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="US bans export of advanced AI chips to China", session_id="test-tech")
        state = await TechnologyAgent().run(state, focus="semiconductor industry and AI development impact")
        o = state.agent_outputs.get("Technology Agent")
        if o: print(f"✅ Technology Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
