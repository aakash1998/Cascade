"""agents/domain/manufacturing.py — Manufacturing Agent"""
from agents.domain._base_domain import DomainAgent

class ManufacturingAgent(DomainAgent):
    name          = "Manufacturing Agent"
    domain        = "manufacturing"
    tier          = "tier2"
    system_prompt = "You are an industrial economist tracking factory output, capacity utilisation, reshoring trends, robotics adoption, and manufacturing sector employment. Respond with valid JSON only."
