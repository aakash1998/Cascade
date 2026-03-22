"""agents/domain/energy.py — Energy Agent"""
from agents.domain._base_domain import DomainAgent

class EnergyAgent(DomainAgent):
    name          = "Energy Agent"
    domain        = "energy"
    tier          = "tier2"
    system_prompt = "You are a senior energy market analyst specialising in oil, gas, coal, renewables, and electricity grids. You track OPEC decisions, energy transition trends, and power infrastructure. Respond with valid JSON only."
