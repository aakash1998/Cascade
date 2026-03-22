"""agents/domain/geopolitics.py — Geopolitics Agent"""
from agents.domain._base_domain import DomainAgent

class GeopoliticsAgent(DomainAgent):
    name          = "Geopolitics Agent"
    domain        = "geopolitics"
    tier          = "tier2"
    system_prompt = "You are a geopolitical risk analyst tracking international relations, sanctions, military conflicts, diplomatic alliances, and their economic spillovers. Respond with valid JSON only."
