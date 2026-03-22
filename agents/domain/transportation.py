"""agents/domain/transportation.py — Transportation Agent"""
from agents.domain._base_domain import DomainAgent

class TransportationAgent(DomainAgent):
    name          = "Transportation Agent"
    domain        = "transportation"
    tier          = "tier2"
    system_prompt = "You are a logistics economist tracking freight rates, shipping lane disruptions, airline capacity, infrastructure investment, and transportation cost pass-through. Respond with valid JSON only."
