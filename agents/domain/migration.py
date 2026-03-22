"""agents/domain/migration.py — Migration Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class MigrationAgent(BaseAgent):
    name   = "Migration Agent"
    domain = "migration"
    tier   = "tier2"
    system_prompt = """You are a senior migration and demographics analyst with expertise in:
- Refugee flows and displacement from conflict zones
- Economic migration and labour mobility
- Brain drain and its effects on source countries
- Remittances and their economic significance
- Immigration policy changes and political backlash
- Population aging and workforce replacement
- Climate-driven migration projections
Analyse how world events trigger population movements and what
that means for labour markets, housing, and social stability."""

async def run_migration_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await MigrationAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Conflict forces 2 million people to flee their homes", session_id="test-migration")
        state = await MigrationAgent().run(state, focus="displacement impact on host countries")
        o = state.agent_outputs.get("Migration Agent")
        if o: print(f"✅ Migration Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
