"""agents/domain/trade.py — Trade Agent"""
from agents.domain._base_domain import DomainAgent

class TradeAgent(DomainAgent):
    name          = "Trade Agent"
    domain        = "trade"
    tier          = "tier2"
    system_prompt = "You are a global trade economist specialising in tariffs, trade deficits, WTO rules, supply chain reshoring, and bilateral trade agreements. Respond with valid JSON only."
