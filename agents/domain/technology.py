"""agents/domain/technology.py — Technology Agent"""
from agents.domain._base_domain import DomainAgent

class TechnologyAgent(DomainAgent):
    name          = "Technology Agent"
    domain        = "technology"
    tier          = "tier2"
    system_prompt = "You are a technology sector analyst tracking semiconductor supply, AI adoption, tech company earnings, cloud spending, cybersecurity, and digital infrastructure. Respond with valid JSON only."
