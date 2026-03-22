"""agents/domain/housing.py — Housing Agent"""
from agents.domain._base_domain import DomainAgent

class HousingAgent(DomainAgent):
    name          = "Housing Agent"
    domain        = "housing"
    tier          = "tier2"
    system_prompt = "You are a real estate economist tracking housing prices, mortgage rates, construction starts, rental markets, affordability, and housing supply in major cities. Respond with valid JSON only."
