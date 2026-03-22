"""agents/domain/mental_health.py — Mental Health Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class MentalHealthAgent(BaseAgent):
    name   = "Mental Health Agent"
    domain = "mental_health"
    tier   = "tier2"
    system_prompt = """You are a senior public mental health analyst with expertise in:
- Population-level mental health trends during crises
- Economic stress and anxiety, depression, suicide rates
- Addiction and substance abuse during downturns
- Healthcare system capacity for mental health
- Workplace burnout and psychological safety
- Community trauma from disasters and conflicts
- Social isolation and loneliness epidemics
Analyse how world events affect population mental health,
which groups are most vulnerable, and what systems are strained."""

async def run_mental_health_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await MentalHealthAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Mass layoffs hit tech sector — 200,000 jobs lost in one month", session_id="test-mh")
        state = await MentalHealthAgent().run(state, focus="mental health impact on affected workers")
        o = state.agent_outputs.get("Mental Health Agent")
        if o: print(f"✅ Mental Health Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
