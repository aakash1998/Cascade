"""agents/domain/social.py — Social Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class SocialAgent(BaseAgent):
    name   = "Social Agent"
    domain = "social"
    tier   = "tier2"
    system_prompt = """You are a senior sociologist and social analyst with expertise in:
- Public sentiment and trust in institutions
- Political polarisation and social cohesion
- Protest movements and civil unrest triggers
- Inequality trends and their social consequences
- Social media's role in amplifying crises
- Community resilience and social safety nets
- Generational divides in response to economic stress
Analyse how world events affect social stability, public trust,
and community cohesion."""

async def run_social_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await SocialAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Unemployment rises to 15% as recession deepens", session_id="test-social")
        state = await SocialAgent().run(state, focus="social stability and public sentiment")
        o = state.agent_outputs.get("Social Agent")
        if o: print(f"✅ Social Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
