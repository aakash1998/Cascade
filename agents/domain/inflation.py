"""agents/domain/inflation.py — Inflation Agent"""
from agents.domain._base_domain import DomainAgent

class InflationAgent(DomainAgent):
    name          = "Inflation Agent"
    domain        = "inflation"
    tier          = "tier2"
    system_prompt = "You are an inflation economist tracking CPI, PPI, wage-price spirals, commodity cost pass-through, central bank responses, and consumer purchasing power. Respond with valid JSON only."
