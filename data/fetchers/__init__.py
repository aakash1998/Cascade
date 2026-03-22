"""data/fetchers/__init__.py — exports all fetcher functions."""
from data.fetchers.tavily    import fetch_tavily
from data.fetchers.fred      import fetch_fred_indicators
from data.fetchers.finnhub   import fetch_finnhub_data
from data.fetchers.gdelt     import fetch_gdelt_events
from data.fetchers.newsapi   import fetch_newsapi_headlines
from data.fetchers.worldbank import fetch_worldbank_indicators

__all__ = [
    "fetch_tavily",
    "fetch_fred_indicators",
    "fetch_finnhub_data",
    "fetch_gdelt_events",
    "fetch_newsapi_headlines",
    "fetch_worldbank_indicators",
]
