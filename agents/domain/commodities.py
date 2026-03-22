"""agents/domain/commodities.py — Commodities Agent"""
from agents.domain._base_domain import DomainAgent

class CommoditiesAgent(DomainAgent):
    name          = "Commodities Agent"
    domain        = "commodities"
    tier          = "tier2"
    system_prompt = "You are a commodities analyst tracking precious metals, industrial metals, rare earth minerals, soft commodities, and the ripple effects of commodity price shifts. Respond with valid JSON only."
