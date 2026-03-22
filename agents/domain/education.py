"""agents/domain/education.py — Education Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class EducationAgent(BaseAgent):
    name   = "Education Agent"
    domain = "education"
    tier   = "tier2"
    system_prompt = """You are a senior education economist with expertise in:
- University enrollment trends during recessions
- Student debt burdens and graduate employment
- Skills gaps and workforce retraining needs
- AI disruption of education and credentialing
- Education funding cuts during austerity
- International student flows and visa policy
- Vocational training vs degree pathways
Analyse how world events affect education access, student debt,
and the skills pipeline for the economy."""

async def run_education_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await EducationAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="AI automates 40% of entry-level knowledge work", session_id="test-edu")
        state = await EducationAgent().run(state, focus="skills demand and education system response")
        o = state.agent_outputs.get("Education Agent")
        if o: print(f"✅ Education Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
