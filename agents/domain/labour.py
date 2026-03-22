"""agents/domain/labour.py — Labour Agent"""
from agents.domain._base_domain import DomainAgent

class LabourAgent(DomainAgent):
    name          = "Labour Agent"
    domain        = "labour"
    tier          = "tier2"
    system_prompt = "You are a labour economist tracking employment trends, wage growth, automation impacts, hiring freezes, union activity, and skills shortages across industries and geographies. Respond with valid JSON only."
