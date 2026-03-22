"""agents/domain/culture.py — Culture Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class CultureAgent(BaseAgent):
    name   = "Culture Agent"
    domain = "culture"
    tier   = "tier2"
    system_prompt = """You are a senior cultural analyst with expertise in:
- Religious and cultural tensions in multi-ethnic societies
- Nationalism and identity politics as economic forces
- Cultural boycotts and their trade consequences
- Value system shifts across generations
- Cultural industries (tourism, entertainment, sports) as economic signals
- Community cohesion during stress
- Cultural responses to technological disruption
Analyse how world events activate cultural fault lines,
trigger identity-based conflicts, and affect social cohesion."""

async def run_culture_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await CultureAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Religious tensions escalate following political crisis", session_id="test-culture")
        state = await CultureAgent().run(state, focus="social cohesion and economic consequences")
        o = state.agent_outputs.get("Culture Agent")
        if o: print(f"✅ Culture Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())