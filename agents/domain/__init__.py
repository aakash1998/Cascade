"""
agents/domain/__init__.py — Domain agent registry
==================================================
Maps domain keys (from the Orchestrator manifest) to agent classes.
The pipeline node uses DOMAIN_REGISTRY to instantiate agents by key.

Usage:
  from agents.domain import DOMAIN_REGISTRY, get_agent

  agent_class = DOMAIN_REGISTRY.get("energy")
  if agent_class:
      agent = agent_class()
      output = await agent.run(state)
"""

from agents.domain.energy        import EnergyAgent
from agents.domain.trade         import TradeAgent
from agents.domain.labour        import LabourAgent
from agents.domain.finance       import FinanceAgent
from agents.domain.inflation     import InflationAgent
from agents.domain.supply_chain  import SupplyChainAgent
from agents.domain.geopolitics   import GeopoliticsAgent
from agents.domain.technology    import TechnologyAgent
from agents.domain.housing       import HousingAgent
from agents.domain.healthcare    import HealthcareAgent
from agents.domain.agriculture   import AgricultureAgent
from agents.domain.environment   import EnvironmentAgent
from agents.domain.currency_fx   import CurrencyFxAgent
from agents.domain.manufacturing import ManufacturingAgent
from agents.domain.retail        import RetailAgent
from agents.domain.government    import GovernmentAgent
from agents.domain.immigration   import ImmigrationAgent
from agents.domain.education     import EducationAgent
from agents.domain.security      import SecurityAgent
from agents.domain.commodities   import CommoditiesAgent
from agents.domain.transportation import TransportationAgent
from agents.domain.demographics  import DemographicsAgent
from agents.domain.media         import MediaAgent

DOMAIN_REGISTRY: dict = {
    "energy":         EnergyAgent,
    "trade":          TradeAgent,
    "labour":         LabourAgent,
    "finance":        FinanceAgent,
    "inflation":      InflationAgent,
    "supply_chain":   SupplyChainAgent,
    "geopolitics":    GeopoliticsAgent,
    "technology":     TechnologyAgent,
    "housing":        HousingAgent,
    "healthcare":     HealthcareAgent,
    "agriculture":    AgricultureAgent,
    "environment":    EnvironmentAgent,
    "currency_fx":    CurrencyFxAgent,
    "manufacturing":  ManufacturingAgent,
    "retail":         RetailAgent,
    "government":     GovernmentAgent,
    "immigration":    ImmigrationAgent,
    "education":      EducationAgent,
    "security":       SecurityAgent,
    "commodities":    CommoditiesAgent,
    "transportation": TransportationAgent,
    "demographics":   DemographicsAgent,
    "media":          MediaAgent,
}


def get_agent(key: str):
    """Returns an instantiated agent for the given domain key, or None."""
    cls = DOMAIN_REGISTRY.get(key)
    return cls() if cls else None
