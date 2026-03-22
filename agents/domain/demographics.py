"""agents/domain/demographics.py — Demographics Agent"""
from agents.domain._base_domain import DomainAgent

class DemographicsAgent(DomainAgent):
    name          = "Demographics Agent"
    domain        = "demographics"
    tier          = "tier2"
    system_prompt = "You are a demographic analyst tracking population ageing, birth rates, urbanisation, generational wealth transfers, and long-run demographic impacts on economies. Respond with valid JSON only."
