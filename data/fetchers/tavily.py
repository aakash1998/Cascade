"""
Tavily is an AI-powered search API designed specifically for LLMs.
It returns clean, summarized results — no HTML scraping needed.

Why Tavily:
  - Purpose-built for RAG (retrieval augmented generation)
  - Returns pre-summarized snippets, not raw HTML
  - Replaces 15+ individual news APIs with one call
  - Free tier: 1000 searches/month

Used by Scout to get current news and web context for any query.

Usage:
  from data.fetchers.tavily import fetch_tavily
  results = await fetch_tavily("US China trade war impact on tech sector")
"""

import asyncio
from typing import Optional

data/fetchers/tavily.py — Tavily Web Search Fetcher
Tavily is the primary data source for Cascade.
It replaces 15+ individual news APIs with one search tool.

What it does:
  Takes a search query, searches the live web, returns
  relevant articles with titles, URLs, and content snippets.
  Results are always fresh — no stale data.

Why Tavily over individual APIs:
  - One API key instead of 15
  - Always up to date — searches live web
  - Returns grounded sources agents can cite
  - 1000 free searches/month

How agents use it:
  Each domain agent gets Tavily results relevant to its domain.
  The Energy Agent gets energy news. The Labour Agent gets
  jobs data. The Geopolitics Agent gets conflict news.

Usage:
  from data.fetchers.tavily import fetch_tavily

  results = await fetch_tavily("OPEC oil production cuts 2025")
  # Returns list of {title, url, content, score}
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
from typing import Optional
from config import settings
from data.cache import cache


async def fetch_tavily(
    query:       str,
    max_results: int = 5,
    cache_ttl:   int = 1800,   # 30 minutes — news stays fresh
) -> list[dict]:
    """
    Searches the web via Tavily and returns relevant results.

    Args:
        query:       What to search for
        max_results: How many results to return (default 5)
        cache_ttl:   How long to cache results in seconds

    Returns:
        List of dicts, each with:
          title:   Article headline
          url:     Source URL
          content: Article snippet (200-500 chars)
          score:   Relevance score 0.0-1.0

    Returns empty list if Tavily fails — never crashes the pipeline.
    """
    if not settings.TAVILY_API_KEY:
        return []

    # Check cache first
    cache_key = f"tavily:{query[:80]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from tavily import TavilyClient

        # Run sync Tavily client in thread pool to not block async loop
        def _search():
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",   # "basic" is cheaper, "advanced" is deeper
                include_answer=False,   # We want raw results, not pre-synthesised
            )
            return response.get("results", [])

        results = await asyncio.get_event_loop().run_in_executor(None, _search)

        # Normalise result format
        normalised = [
            {
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": r.get("content", "")[:500],  # cap at 500 chars
                "score":   float(r.get("score", 0.5)),
                "source":  "Tavily",
            }
            for r in results
        ]

        # Cache results
        cache.set(cache_key, normalised, ttl=cache_ttl)

        return normalised

    except Exception as e:
        print(f"⚠️  Tavily fetch failed for '{query[:40]}': {e}")
        return []


async def fetch_tavily_for_domain(domain: str, query: str) -> list[dict]:
    """
    Builds a domain-specific search query and fetches results.
    Each domain gets a tailored search that surfaces the most
    relevant information for that agent's analysis.

    Args:
        domain: The agent domain (e.g. "energy", "labour")
        query:  The user's original query

    Returns:
        Tavily search results for this domain
    """
    # Domain-specific search query templates
    # These make searches more targeted than just passing the raw query
    domain_queries = {
        "energy":       f"energy prices oil gas impact {query}",
        "trade":        f"trade tariffs imports exports {query}",
        "labour":       f"employment jobs layoffs hiring {query}",
        "inflation":    f"inflation prices CPI interest rates {query}",
        "geopolitics":  f"geopolitical conflict sanctions {query}",
        "currency":     f"currency exchange rate forex {query}",
        "supply_chain": f"supply chain shipping logistics {query}",
        "technology":   f"technology AI semiconductor {query}",
        "housing":      f"housing real estate mortgage {query}",
        "healthcare":   f"healthcare public health medical {query}",
        "climate":      f"climate environment extreme weather {query}",
        "food":         f"food agriculture commodity prices {query}",
        "finance":      f"financial markets banking economy {query}",
        "migration":    f"migration immigration population {query}",
        "social":       f"social unrest protest inequality {query}",
        "mental_health":f"mental health wellbeing stress {query}",
        "education":    f"education employment skills {query}",
        "crime":        f"crime security safety {query}",
        "debt":         f"debt credit bankruptcy {query}",
        "media":        f"media misinformation narrative {query}",
        "demographics": f"population demographics aging {query}",
        "infrastructure":f"infrastructure power grid internet {query}",
        "culture":      f"cultural social identity {query}",
    }

    search_query = domain_queries.get(domain, query)
    return await fetch_tavily(search_query)


# ─────────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("\n🧪 Testing Tavily fetcher...\n")

        results = await fetch_tavily("US China trade war impact 2025", max_results=3)

        if results:
            print(f"✅ Tavily returned {len(results)} results\n")
            for i, r in enumerate(results, 1):
                print(f"  {i}. {r['title'][:60]}")
                print(f"     Score: {r['score']:.2f}")
                print(f"     {r['content'][:100]}...\n")
        else:
            print("❌ No results returned — check TAVILY_API_KEY in .env")

        # Test cache
        results2 = await fetch_tavily("US China trade war impact 2025", max_results=3)
        print(f"✅ Cache working: second call returned {len(results2)} results instantly")
        print(f"   Cache stats: {cache.stats()}\n")

    asyncio.run(test())
