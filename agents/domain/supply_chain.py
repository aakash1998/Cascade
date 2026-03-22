"""agents/domain/supply_chain.py — Supply Chain Agent"""
from agents.domain._base_domain import DomainAgent

class SupplyChainAgent(DomainAgent):
    name          = "Supply Chain Agent"
    domain        = "supply_chain"
    tier          = "tier2"
    system_prompt = "You are a supply chain expert tracking manufacturing logistics, port congestion, inventory levels, just-in-time vs just-in-case shifts, and nearshoring trends. Respond with valid JSON only."
