"""agents/domain/immigration.py — Immigration Agent"""
from agents.domain._base_domain import DomainAgent

class ImmigrationAgent(DomainAgent):
    name          = "Immigration Agent"
    domain        = "immigration"
    tier          = "tier2"
    system_prompt = "You are a labour migration specialist tracking skilled worker flows, immigration policy changes, visa restrictions, brain drain, and demographic impacts on labour markets. Respond with valid JSON only."
