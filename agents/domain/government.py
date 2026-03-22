"""agents/domain/government.py — Government Agent"""
from agents.domain._base_domain import DomainAgent

class GovernmentAgent(DomainAgent):
    name          = "Government Agent"
    domain        = "government"
    tier          = "tier2"
    system_prompt = "You are a fiscal policy analyst tracking government spending, tax policy, deficit financing, regulatory changes, and stimulus measures and their macroeconomic effects. Respond with valid JSON only."
