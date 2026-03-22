"""agents/domain/security.py — Security Agent"""
from agents.domain._base_domain import DomainAgent

class SecurityAgent(DomainAgent):
    name          = "Security Agent"
    domain        = "security"
    tier          = "tier2"
    system_prompt = "You are a defence and security analyst tracking military spending, cybersecurity threats, intelligence sharing, arms exports, and the economic impact of security policy. Respond with valid JSON only."
