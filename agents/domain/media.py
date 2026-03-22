"""agents/domain/media.py — Media Agent"""
from agents.domain._base_domain import DomainAgent

class MediaAgent(DomainAgent):
    name          = "Media Agent"
    domain        = "media"
    tier          = "tier2"
    system_prompt = "You are a media and information economist tracking news sentiment, social media narratives, public opinion shifts, misinformation risks, and how narrative shapes market behaviour. Respond with valid JSON only."
