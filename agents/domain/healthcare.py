"""agents/domain/healthcare.py — Healthcare Agent"""
from agents.domain._base_domain import DomainAgent

class HealthcareAgent(DomainAgent):
    name          = "Healthcare Agent"
    domain        = "healthcare"
    tier          = "tier2"
    system_prompt = "You are a healthcare economist tracking pharmaceutical costs, hospital capacity, public health policy, insurance markets, and biotech sector trends. Respond with valid JSON only."
