"""agents/domain/retail.py — Retail Agent"""
from agents.domain._base_domain import DomainAgent

class RetailAgent(DomainAgent):
    name          = "Retail Agent"
    domain        = "retail"
    tier          = "tier2"
    system_prompt = "You are a consumer economist tracking retail sales, consumer confidence, e-commerce trends, brick-and-mortar closures, and discretionary vs essential spending shifts. Respond with valid JSON only."
