"""agents/domain/healthcare.py — Healthcare Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class HealthcareAgent(BaseAgent):
    name   = "Healthcare Agent"
    domain = "healthcare"
    tier   = "tier2"
    system_prompt = """You are a senior public health and healthcare economist with expertise in:
- Disease outbreaks, pandemics, and health system capacity
- Pharmaceutical supply chains and drug pricing
- Healthcare workforce shortages and burnout
- Health insurance costs and coverage gaps
- Government healthcare spending and austerity
- Mental health system capacity
- Biotech and pharma investment cycles
Analyse how world events strain health systems, affect drug availability,
and change healthcare costs for individuals."""

async def run_healthcare_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await HealthcareAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="New respiratory virus spreads across three continents", session_id="test-health")
        state = await HealthcareAgent().run(state, focus="health system capacity and economic impact")
        o = state.agent_outputs.get("Healthcare Agent")
        if o: print(f"✅ Healthcare Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
