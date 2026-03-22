"""agents/domain/media.py — Media Domain Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agents.base_agent import BaseAgent
from graph.state import CascadeState

class MediaAgent(BaseAgent):
    name   = "Media Agent"
    domain = "media"
    tier   = "tier2"
    system_prompt = """You are a senior media analyst and disinformation researcher with expertise in:
- Narrative framing and its economic consequences
- State-sponsored disinformation campaigns
- Social media amplification of fear and panic
- Press freedom erosion during crises
- Censorship and information blackouts
- Market-moving misinformation (rumours, fake news)
- Public trust in media and its collapse
Analyse how world events are shaped and distorted by media narratives,
and how information (or misinformation) creates secondary economic effects."""

async def run_media_agent(state: CascadeState, focus: str = "") -> CascadeState:
    return await MediaAgent().run(state, focus)

if __name__ == "__main__":
    import asyncio
    from graph.state import create_initial_state
    async def test():
        state = create_initial_state(query="Viral misinformation causes bank run fears", session_id="test-media")
        state = await MediaAgent().run(state, focus="information contagion and market impact")
        o = state.agent_outputs.get("Media Agent")
        if o: print(f"✅ Media Agent\n   Confidence: {o.confidence:.2f}\n   Finding: {o.finding[:150]}")
    asyncio.run(test())
