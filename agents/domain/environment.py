"""agents/domain/environment.py — Environment Agent"""
from agents.domain._base_domain import DomainAgent

class EnvironmentAgent(DomainAgent):
    name          = "Environment Agent"
    domain        = "environment"
    tier          = "tier2"
    system_prompt = "You are an environmental economist tracking carbon prices, climate policy, ESG regulations, green energy subsidies, and physical climate risk to industries. Respond with valid JSON only."
