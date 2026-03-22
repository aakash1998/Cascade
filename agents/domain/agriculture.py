"""agents/domain/agriculture.py — Agriculture Agent"""
from agents.domain._base_domain import DomainAgent

class AgricultureAgent(DomainAgent):
    name          = "Agriculture Agent"
    domain        = "agriculture"
    tier          = "tier2"
    system_prompt = "You are an agricultural economist tracking food commodity prices, crop yields, fertiliser costs, food security, weather impacts, and farm subsidies. Respond with valid JSON only."
