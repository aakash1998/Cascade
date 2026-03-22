"""agents/domain/finance.py — Finance Agent"""
from agents.domain._base_domain import DomainAgent

class FinanceAgent(DomainAgent):
    name          = "Finance Agent"
    domain        = "finance"
    tier          = "tier2"
    system_prompt = "You are a financial analyst tracking central bank policy, credit markets, banking sector health, equity markets, bond yields, and systemic risk. Respond with valid JSON only."
