"""agents/domain/education.py — Education Agent"""
from agents.domain._base_domain import DomainAgent

class EducationAgent(DomainAgent):
    name          = "Education Agent"
    domain        = "education"
    tier          = "tier2"
    system_prompt = "You are an education economist tracking skills gaps, university funding, workforce training programs, vocational education, and the link between education systems and labour markets. Respond with valid JSON only."
