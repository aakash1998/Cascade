"""agents/domain/currency_fx.py — Currency/FX Agent"""
from agents.domain._base_domain import DomainAgent

class CurrencyFxAgent(DomainAgent):
    name          = "Currency/FX Agent"
    domain        = "currency_fx"
    tier          = "tier2"
    system_prompt = "You are a foreign exchange analyst tracking USD strength, exchange rate volatility, currency intervention, petrodollar flows, and FX impact on imports and exports. Respond with valid JSON only."
