# 🌊 Cascade — The Ripple Effect Engine

> Type any world event. Watch a network of AI agents trace every ripple — across economies, jobs, industries, politics, and your personal life — in real time.

**"What does the US-China trade war mean for a software engineer in Calgary?"**
Ask it. Watch up to 31 agents think live. See the chain unfold. Three scenarios modelled. Every claim sourced. Accuracy tracked.

---

## 📋 Table of Contents

1. [What Is Cascade](#1-what-is-cascade)
2. [How It Works — The Big Picture](#2-how-it-works--the-big-picture)
3. [Agent Architecture — Full Roster](#3-agent-architecture--full-roster)
4. [Dynamic Agent Count — Dimensional Complexity Scoring](#4-dynamic-agent-count--dimensional-complexity-scoring)
5. [The Ripple Chain — How Agents Connect](#5-the-ripple-chain--how-agents-connect)
6. [Scenario Branching — Best · Base · Worst](#6-scenario-branching--best--base--worst)
7. [Agent Debate Round](#7-agent-debate-round)
8. [Historical Pattern Matching](#8-historical-pattern-matching)
9. [Counterfactual Analysis](#9-counterfactual-analysis)
10. [Knowledge Graph](#10-knowledge-graph)
11. [Real-Time Streaming — How the UI Works](#11-real-time-streaming--how-the-ui-works)
12. [User Onboarding — 7 Questions](#12-user-onboarding--7-questions)
13. [Conversation Memory](#13-conversation-memory)
14. [Data Sources — 40+ Free Sources](#14-data-sources--40-free-sources)
15. [LLM Strategy — Near Zero Cost](#15-llm-strategy--near-zero-cost)
16. [Trust Layer — Source Citation + Confidence](#16-trust-layer--source-citation--confidence)
17. [The Feedback Loop — Prediction Tracking](#17-the-feedback-loop--prediction-tracking)
18. [Error Handling + Edge Cases](#18-error-handling--edge-cases)
19. [Hallucination Guardrails — 3 Layers](#19-hallucination-guardrails--3-layers)
20. [Human Notification System](#20-human-notification-system)
21. [Sharing + Virality Features](#21-sharing--virality-features)
22. [Alert + Watchlist System](#22-alert--watchlist-system)
23. [Comparison Mode](#23-comparison-mode)
24. [Tech Stack](#24-tech-stack)
25. [Project Folder Structure](#25-project-folder-structure)
26. [Running Locally](#26-running-locally)
27. [How Others Can Use This](#27-how-others-can-use-this)
28. [Protecting Your API Keys](#28-protecting-your-api-keys)
29. [Cost Management](#29-cost-management)
30. [Pre-flight Checklist](#30-pre-flight-checklist)

---

## 1. What Is Cascade

Cascade is a multi-agent AI system that takes any world event and traces its ripple effects across interconnected global systems — economics, geopolitics, supply chains, labour markets, mental health, social stability, and personal impact — in real time.

It is not a chatbot. It is not a search engine. It is a structured thinking machine composed of many specialist agents, each an expert in one domain, all working in parallel and feeding results into each other — grounded in 40+ real data sources, with every claim sourced, every prediction logged, and every outcome eventually verified.

### What makes it different

| Feature | ChatGPT / Claude | Cascade |
|---|---|---|
| Agents | 1 | Up to 31 |
| Domains covered | All at once, shallowly | Each domain deeply |
| Data grounding | Training data only | 40+ live free APIs |
| Scenarios | 1 answer | Best · Base · Worst |
| Source citation | Rarely | Every claim |
| Prediction tracking | Never | Always — with verification |
| Personal impact | Generic | Tailored to your job, city, family |
| Agent debate | No | Yes — agents challenge each other |
| Historical patterns | No | Yes — finds similar past events |

---

## 2. How It Works — The Big Picture

```
User types query
       │
       ▼
┌──────────────────────────────────────────┐
│  ONBOARDING (first visit only — 90 sec)  │
│  7 questions: job · city · sector ·      │
│  family · housing · income · extras      │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  QUERY ANALYSER — Intent + Complexity    │
│                                          │
│  • Detect query intent                   │
│  • Score 5 complexity dimensions         │
│  • Look up knowledge graph relationships │
│  • Find similar historical events        │
│  • Return agent manifest (JSON)          │
└────────────────────┬─────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  ┌─────────────┐       ┌─────────────────┐
  │ SCOUT runs  │       │ KNOWLEDGE GRAPH │
  │ parallel    │       │ queried for     │
  │ data fetch  │       │ relationships   │
  │ from 40+    │       │ between domains │
  │ free APIs   │       └─────────────────┘
  └──────┬──────┘
         │ shared data context
         ▼
┌──────────────────────────────────────────┐
│  DOMAIN AGENTS run in parallel           │
│  (8–23 conditional agents)               │
│  Each reads: query + profile +           │
│  data context + knowledge graph          │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  DEBATE ROUND (1 cycle)                  │
│  Conflicting agents surface and          │
│  argue — output is richer + honest       │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  CONNECTOR builds ripple chain           │
│  HISTORIAN finds 3 similar past events   │
│  SCENARIO BUILDER forks into 3 branches  │
│  COUNTERFACTUAL adds "what if" analysis  │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  WATCHDOG checks every claim vs data     │
│  CONFIDENCE RATER scores every ripple    │
│  BIAS CHECKER flags data source gaps     │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  PERSONALISER applies user profile       │
│  SUMMARISER writes plain-language output │
│  PREDICTION LOGGER stores every claim    │
└────────────────────┬─────────────────────┘
                     │
                     ▼
         Streamed live to frontend
         Shareable link generated
         Watchlist updated if applicable
```

---

## 3. Agent Architecture — Full Roster

### Permanent agents — always run (10 agents)

| Agent | Role |
|---|---|
| Orchestrator | Analyses query · scores complexity · returns agent manifest |
| Scout | Fetches live data from all APIs before agents run |
| Knowledge Graph | Queries relationship map between domains and countries |
| Connector | Builds directed ripple chain from all agent outputs |
| Debate Moderator | Surfaces conflicts between agents · runs one debate cycle |
| Historian | Finds 3 most similar past events + what happened |
| Scenario Builder | Forks chain into best · base · worst case |
| Watchdog | Checks every claim against fetched data · flags unsupported |
| Confidence Rater | Scores 0–100% confidence on every ripple claim |
| Personaliser | Applies user profile — "what this means for YOU" |
| Bias Checker | Flags where data coverage is thin or Western-centric |
| Summariser | Writes final plain-language 5-sentence summary |
| Prediction Logger | Logs every verifiable claim with timestamp for tracking |

### Conditional domain agents — spun up dynamically (23 agents)

| Agent | Domain | Key signals it monitors |
|---|---|---|
| Energy | Oil · gas · electricity · renewables | OPEC decisions · pipeline disruptions · green policy |
| Trade | Tariffs · imports · exports · WTO | Trade wars · sanctions · supply chain shifts |
| Labour | Jobs · wages · layoffs · automation | Hiring signals · unemployment filings · AI displacement |
| Inflation | CPI · purchasing power · prices | Interest rates · supply shocks · commodity prices |
| Geopolitics | Conflicts · alliances · diplomacy | Wars · elections · regime changes · treaties |
| Currency | Forex · exchange rates · reserves | Sanctions · capital flows · trade imbalances |
| Supply Chain | Manufacturing · shipping · logistics | Port activity · freight rates · factory closures |
| Technology | AI · semiconductors · cyber · patents | Chip bans · AI regulation · tech investment |
| Housing | Real estate · mortgage · rent · construction | Rate hikes · migration · economic downturns |
| Healthcare | Public health · pharma · insurance · biotech | Pandemics · drug pricing · healthcare policy |
| Climate | Carbon · energy transition · extreme weather | Climate policy · natural disasters · ESG shifts |
| Food | Agriculture · commodities · famine · supply | Droughts · conflict in farming regions · fertiliser |
| Finance | Markets · banking · debt · investment | Rate hikes · bank failures · sovereign debt |
| Migration | Population flow · demographics · labour | Wars · climate collapse · economic migration |
| Social | Sentiment · polarisation · unrest · media | Elections · inequality · misinformation · protests |
| Mental Health | Wellbeing · addiction · crisis services | Unemployment · isolation · social instability |
| Education | Enrollment · student debt · skills gap | Economic downturns · AI disruption · policy |
| Crime + Safety | Crime rates · policing · justice | Inequality · unemployment · political instability |
| Debt + Credit | Personal debt · bankruptcies · credit access | Rate hikes · job losses · housing crashes |
| Media + Information | Propaganda · censorship · narratives | Conflicts · elections · platform policy changes |
| Demographics | Birth rates · aging · workforce composition | Policy · migration · economic conditions |
| Infrastructure | Power grids · roads · internet · water | Wars · climate · funding cuts |
| Religion + Culture | Cultural tensions · identity · institutions | Migration · conflict · political shifts |

**Maximum total agents: 10 permanent + 23 conditional = 33**

---

## 4. Dynamic Agent Count — Dimensional Complexity Scoring

Instead of a simple 1–10 number, the Orchestrator scores 5 independent dimensions. This is more honest, more explainable, and more accurate.

```python
class ComplexityScore:
    geographic_scope: float    # 1=local · 3=regional · 5=global
    domain_breadth: float      # count of affected domains × 1.5
    causal_chain_depth: float  # steps removed from direct impact
    time_horizon: float        # 1=days · 3=months · 5=years+
    personal_relevance: float  # how directly user profile is affected

WEIGHTS = {
    'geographic_scope':  0.20,
    'domain_breadth':    0.30,  # most important
    'causal_chain_depth': 0.25,
    'time_horizon':      0.10,
    'personal_relevance': 0.15
}

def total_score(c: ComplexityScore) -> float:
    return (
        c.geographic_scope   * WEIGHTS['geographic_scope']   +
        c.domain_breadth     * WEIGHTS['domain_breadth']     +
        c.causal_chain_depth * WEIGHTS['causal_chain_depth'] +
        c.time_horizon       * WEIGHTS['time_horizon']       +
        c.personal_relevance * WEIGHTS['personal_relevance']
    )
    # Returns 1.0–5.0
```

### Agent count from complexity score

| Score | Conditional agents | Example |
|---|---|---|
| 1.0–2.0 | 3–5 | "What does a Fed rate cut mean for me?" |
| 2.1–3.0 | 6–10 | "How does UK inflation affect European housing?" |
| 3.1–4.0 | 11–16 | "What does the Russia-Ukraine war mean for energy?" |
| 4.1–5.0 | 17–23 | "How do AI layoffs, inflation, and the Middle East war connect for a nurse in Toronto?" |

### Query intent detection

The Orchestrator also detects intent and adjusts agent configuration:

```python
INTENTS = {
    "personal_impact":    ["mean for me", "affect me", "my job", "my family"],
    "prediction":         ["what will happen", "forecast", "predict"],
    "causal_chain":       ["why", "caused by", "because of"],
    "historical":         ["history of", "in the past", "last time"],
    "comparison":         ["vs", "compared to", "difference between"],
    "counterfactual":     ["what if", "if X happens", "suppose"],
    "sector_specific":    ["for tech", "for healthcare", "for finance"]
}
```

Different intents activate different permanent agents:
- `counterfactual` intent → Counterfactual agent activated
- `historical` intent → Historian weighted more heavily
- `comparison` intent → Two parallel ripple chains run simultaneously

---

## 5. The Ripple Chain — How Agents Connect

Each domain agent returns a structured output:

```python
@dataclass
class AgentOutput:
    domain: str
    finding: str                    # plain language analysis
    confidence: float               # 0.0–1.0
    sources: List[str]              # which data sources support this
    data_points: List[DataPoint]    # specific figures cited
    downstream_signals: List[str]   # which domains are next affected
    timeframe: str                  # when this ripple hits
    severity: str                   # low · medium · high · critical
    uncertainty_note: str           # what would change this analysis
    contradicting_view: str         # the other side of the argument
```

The `downstream_signals` field is how the chain builds. Each agent tells the Connector which domains it thinks will be affected next. The Connector uses these to build a directed graph.

### Chain example

```
Query: US-China trade war

Tier 1 — direct:
  Trade     → tariffs on tech goods rise 25%         [confidence: 0.91]
  Tech      → semiconductor supply restricted         [confidence: 0.88]
  Geopolitics → alliance tensions rise                [confidence: 0.84]

Tier 2 — fed by Tier 1:
  Labour    → Canadian tech hiring slows              [confidence: 0.74]
  Inflation → consumer electronics +12%              [confidence: 0.79]
  Currency  → CAD weakens vs USD 3–5%                [confidence: 0.68]
  Supply Chain → alternative sourcing accelerates    [confidence: 0.71]

Tier 3 — fed by Tier 2:
  Housing   → tech hub real estate softens           [confidence: 0.52]
  Mental Health → job insecurity stress increases    [confidence: 0.48]
  Education → STEM enrollment signals mixed          [confidence: 0.44]
  Social    → anti-China sentiment rises in media    [confidence: 0.61]

Personalised for: Software engineer · Calgary · Tech sector · Family with mortgage:
  "Your sector shows hiring slowdown signals (3–6 month lag).
   Your mortgage payment is unaffected short-term but rate sensitivity increases.
   Tech goods you buy will cost ~12% more within 6 months.
   Your income is not immediately at risk but your employer's pipeline may shrink."
```

---

## 6. Scenario Branching — Best · Base · Worst

Every analysis produces three versions of the ripple chain. The Scenario Builder runs after the Connector and forks the chain based on key variable assumptions.

```python
SCENARIO_DEFINITIONS = {
    "best_case": {
        "description": "Key tensions resolve faster than expected",
        "key_assumptions": [
            "Trade deal reached within 6 months",
            "No military escalation",
            "Central banks coordinate policy"
        ]
    },
    "base_case": {
        "description": "Current trajectory continues",
        "key_assumptions": [
            "Situation remains as-is for 12 months",
            "No major surprises in either direction"
        ]
    },
    "worst_case": {
        "description": "Escalation or additional shocks occur",
        "key_assumptions": [
            "Military conflict expands",
            "Additional sanctions imposed",
            "Recession triggers in key economies"
        ]
    }
}
```

The UI shows all three scenarios side by side with a toggle. The user sees clearly: "In the best case your job is fine. In the worst case your sector loses 15% of positions."

---

## 7. Agent Debate Round

After all domain agents complete their first pass, the Debate Moderator scans for contradictions and surfaces them.

```python
DEBATE_TRIGGER_CONDITIONS = [
    "two agents predict opposite outcomes for the same domain",
    "confidence scores differ by more than 0.3 for the same claim",
    "one agent's downstream signal contradicts another agent's finding",
    "historical pattern suggests opposite outcome to current analysis"
]
```

When triggered, the two conflicting agents each get one more prompt:

```
Labour Agent said: "Tech hiring in Canada will slow significantly."
Finance Agent said: "Canadian markets are resilient — employment will hold."

Each agent: Review the other's argument. Where do you agree? 
Where do you disagree and why? What evidence supports your view?
Max 150 words.
```

The Connector then presents both views to the user with the evidence for each. This is enormously more honest than presenting one confident answer. It also makes the output far more interesting to read.

---

## 8. Historical Pattern Matching

The Historian agent runs in parallel with domain agents. It searches a curated database of ~200 major historical events and finds the 3 most similar to the current query.

```python
HISTORICAL_EVENTS_DB = [
    {
        "event": "2018 US-China Trade War (Round 1)",
        "year": 2018,
        "domains": ["trade", "tech", "currency", "labour"],
        "what_happened": {
            "short_term": "Markets fell 20%, supply chains shifted to Vietnam",
            "medium_term": "Tech companies diversified away from China",
            "long_term": "Permanent restructuring of global supply chains"
        },
        "accuracy_verified": True
    },
    {
        "event": "1973 Oil Embargo",
        "year": 1973,
        "domains": ["energy", "inflation", "trade", "geopolitics"],
        ...
    },
    ...
]
```

The output tells users: "The 3 most similar historical events were X, Y, Z. Here is what happened. Here is what was different. Here is what that suggests for today."

This grounds the analysis in reality and dramatically increases credibility.

---

## 9. Counterfactual Analysis

The Counterfactual agent runs when query intent is `counterfactual` or when complexity score is above 3.5.

It models three key "what if" branches:

```
What if China retaliates with their own tariffs?
  → Tech supply chain disruption accelerates
  → USD strengthens further
  → Canadian exports to China fall (agriculture, energy)

What if the US backs down within 6 months?
  → Markets recover, volatility falls
  → Tech supply chain partially restabilises
  → CAD recovers vs USD

What if a third party (EU) intervenes diplomatically?
  → Partial resolution most likely
  → Some tariffs remain as leverage
  → Global supply chain diversification continues
```

Each counterfactual is rated by probability (based on historical precedent and current signals) and shows how the ripple chain changes under each scenario.

---

## 10. Knowledge Graph

The knowledge graph stores structured relationships between countries, sectors, commodities, historical events, and causal connections — built from public data and curated manually.

```python
# NetworkX directed graph — free, runs locally, no database needed
import networkx as nx

G = nx.DiGraph()

# Relationships
G.add_edge("oil_price_rise", "inflation",
           weight=0.85, lag_months=2, direction="positive")
G.add_edge("us_china_tariffs", "semiconductor_supply",
           weight=0.90, lag_months=1, direction="negative")
G.add_edge("ukraine_conflict", "wheat_prices",
           weight=0.88, lag_months=0, direction="positive")
G.add_edge("wheat_prices", "food_insecurity_africa",
           weight=0.76, lag_months=3, direction="positive")
G.add_edge("tech_layoffs", "housing_demand_sf",
           weight=0.65, lag_months=4, direction="negative")

# Country-specific sensitivities
COUNTRY_SENSITIVITIES = {
    "Canada": {
        "oil_price":       0.9,   # high sensitivity — major exporter
        "us_tariffs":      0.95,  # very high — 75% exports go to US
        "wheat_prices":    0.7,   # high — major wheat exporter
        "tech_employment": 0.6
    },
    "Germany": {
        "energy_prices":   0.95,  # very high — energy importer
        "china_trade":     0.8,
        "auto_sector":     0.9
    }
}
```

Before agents run, the Orchestrator queries the knowledge graph for every entity in the query. This pre-populates the shared context with known causal weights, reducing hallucination and improving connection quality.

---

## 11. Real-Time Streaming — How the UI Works

The backend uses Server-Sent Events (SSE) — no WebSockets, no complex setup, built into every browser.

### What the user sees — phase by phase

```
Phase 1: Onboarding (first visit only — takes 90 seconds)
  → 7 questions appear one at a time
  → Stored in localStorage — never asked again

Phase 2: Query submitted
  → "Analysing complexity..."
  → Dimensional scores appear live:
    Geographic: Global (5.0) · Domains: 8 affected (4.0) · Depth: 3 steps (3.5)
  → "Spawning 16 agents..."
  → Agent cards appear, greyed out: "Waiting..."

Phase 3: Data fetching (parallel)
  → "Scout fetching from 12 data sources..."
  → Data sources light up as they respond

Phase 4: Agents stream live (the money shot)
  → Each agent card lights up as it finishes
  → Text streams token by token inside the card
  → Confidence % and key sources appear
  → Connections draw between cards as Connector runs
  → Debate cards appear where agents disagreed

Phase 5: Scenario branches build
  → Three panels appear side by side: Best · Base · Worst
  → Each streams its key differences from the base chain

Phase 6: Historical parallels
  → "Historian found 3 similar past events..."
  → Cards show: what happened then vs what might happen now

Phase 7: Counterfactuals
  → "What if" branches appear with probability scores

Phase 8: Personalised impact
  → Highlighted box: "What this means for YOU"
  → Streams token by token

Phase 9: Summary + trust layer
  → Plain language 5-sentence summary
  → Every claim shows its source on hover
  → Confidence colour coding: green >80% · amber 60–80% · red <60%
  → Shareable link generated
  → Disclaimer shown
  → Prediction logger confirms claims are saved
```

---

## 12. User Onboarding — 7 Questions

Asked once on first visit. Stored in `localStorage` only. Never sent to a server. Never logged.

```
Q1: What do you do for work?
    [Free text]

Q2: What city and country are you in?
    [Free text]

Q3: What sector do you work in?
    [Tech / Healthcare / Finance / Education / Manufacturing /
     Retail / Government / Energy / Agriculture / Other]

Q4: What is your household situation?
    [Single / Couple no kids / Family with kids /
     Single parent / Supporting elderly parents / Other]

Q5: What is your housing situation?
    [Renting / Own with mortgage / Own outright /
     Living with family / Other]

Q6: What is your income bracket? (optional)
    [Under $30k / $30–60k / $60–100k / $100k+ / Skip]

Q7: Anything else that makes your situation unique? (optional)
    [Free text — e.g. "I have savings in USD",
     "I work remotely", "I invest in Canadian oil stocks",
     "My employer is government-funded"]
```

Q7 is the most powerful — it lets people surface things no dropdown could predict. The Personaliser gets a rich profile that produces genuinely personal output.

**If all questions skipped:** Personaliser produces a general population analysis with no personal framing. Still useful. Never forces the user.

---

## 13. Conversation Memory

Memory lives in the Python backend session object, keyed by `session_id` (UUID in `localStorage`).

```python
@dataclass
class SessionMemory:
    session_id: str
    profile: UserProfile
    conversation: List[Turn]        # full history
    active_watchlist: List[str]     # topics being tracked
    knowledge_graph_cache: dict     # pre-fetched relationships
    created_at: datetime
    last_active: datetime

@dataclass
class Turn:
    role: str                       # "user" | "cascade"
    content: str | CascadeOutput
    timestamp: datetime
    agents_used: List[str]
    predictions_logged: List[str]   # IDs of predictions stored
```

Follow-up questions work naturally because every agent receives full conversation history. "What about for someone in Toronto?" or "What changes if inflation stays high for 2 years?" get contextually aware responses.

**Limits:**
- Max 10 turns per session (sliding window after that)
- Session TTL: 2 hours of inactivity
- Everything in RAM — no disk writes
- Page refresh starts fresh session (by design)

---

## 14. Data Sources — 40+ Free Sources

Scout fetches only what is relevant to the query. All fetches run in parallel. A failed fetch returns an empty dict — never a crash.

### Economic + Financial

| Source | Data | Free tier |
|---|---|---|
| FRED (US Federal Reserve) | 800k+ economic series · CPI · unemployment · GDP · rates | Completely free |
| World Bank API | Economic indicators · 196 countries · historical | Completely free |
| IMF Data API | Global financial stability · balance of payments | Completely free |
| Alpha Vantage | 60+ economic indicators · commodities · forex | 25 calls/day free |
| Finnhub | Stocks · forex · crypto · earnings · economic calendar | 60 calls/min free |
| Financial Modeling Prep | GDP · inflation · unemployment · treasury rates | Free tier |
| DBnomics | 20M+ indicators · 80+ statistical agencies aggregated | Completely free |
| OECD Data | OECD country data · economic outlook | Completely free |
| BLS (US Bureau of Labor Stats) | Employment · wages · CPI · productivity | Completely free |
| Eurostat | EU economic data · employment · trade | Completely free |

### Geopolitical + Conflict

| Source | Data | Free tier |
|---|---|---|
| GDELT Project | Every world event · conflict · political · updated 15min | Completely free |
| ACLED | Armed conflict data · political violence · protests | Free for research |
| Global Terrorism Database | Terrorism incidents worldwide | Completely free |
| UNODC | Crime · drugs · corruption · international law | Completely free |
| Uppsala Conflict Data | Organised violence · peace agreements | Completely free |

### News + Sentiment

| Source | Data | Free tier |
|---|---|---|
| NewsAPI | Global headlines · 30 days · 150k sources | 100 calls/day free |
| GDELT News | Real-time global news · translated · 100 languages | Completely free |
| MediaStack | Live news · 50 countries · sentiment | 500 calls/month free |
| Currents API | News · categories · countries | 600 calls/day free |
| The Guardian API | Quality journalism · tagged · searchable | Completely free |
| NY Times API | Archive · search · tags | Completely free |
| RSS Feeds (direct) | BBC · Reuters · AP · Al Jazeera · direct feeds | Completely free |

### Social Signals

| Source | Data | Free tier |
|---|---|---|
| Reddit API (PRAW) | Public posts · comments · sentiment · subreddits | Free with account |
| Google Trends (Pytrends) | Search interest · geographic breakdown | Completely free |
| Hacker News API | Tech community sentiment · trending topics | Completely free |
| Wikipedia Pageviews | What people are reading · proxy for public attention | Completely free |

### Trade + Supply Chain

| Source | Data | Free tier |
|---|---|---|
| UN Comtrade | Global trade flows · bilateral trade data | Free — limited calls |
| World Trade Organization | Tariff data · trade statistics | Completely free |
| UNCTAD | Trade and development statistics | Completely free |
| MarineTraffic (AIS) | Ship positions · port activity | Free tier limited |
| OpenFlights | Airport and route data | Completely free |

### Climate + Environment

| Source | Data | Free tier |
|---|---|---|
| Open-Meteo | Weather · climate · historical | Completely free |
| NASA Earthdata | Climate · satellite · environmental | Completely free |
| NOAA Climate Data | Temperature · precipitation · extreme events | Completely free |
| Global Forest Watch | Deforestation · land use | Completely free |

### Labour + Jobs

| Source | Data | Free tier |
|---|---|---|
| BLS JOLTS | Job openings · quits · layoffs (US) | Completely free |
| Layoffs.fyi (scraped) | Tech layoff tracker | Public data |
| LinkedIn (unofficial) | Job posting trends via scraping | Varies |
| Indeed Hiring Lab API | Labour market insights · job trends | Free for research |
| ILO (Int'l Labour Org) | Global employment · wages · social protection | Completely free |

### Government + Policy

| Source | Data | Free tier |
|---|---|---|
| data.gov (US) | US government open data | Completely free |
| EU Open Data Portal | European policy · legislation | Completely free |
| World Integrated Trade Solution | Trade policy · tariff schedules | Completely free |
| USPTO Patents API | Patent filings · tech innovation signals | Completely free |
| OpenSecrets | US political spending · lobbying | Completely free |

### Health + Wellbeing

| Source | Data | Free tier |
|---|---|---|
| WHO Global Health Observatory | Disease · mortality · health systems | Completely free |
| CDC Wonder | US public health data | Completely free |
| Our World in Data API | Health · poverty · wellbeing across countries | Completely free |

### Reference + Geography

| Source | Data | Free tier |
|---|---|---|
| REST Countries | Country data · currencies · languages · geography | Completely free |
| GeoNames | Geographic data · timezone · coordinates | Free with account |
| Country.io | Country codes · currencies · languages | Completely free |

### How Scout prioritises

```python
SOURCE_PRIORITY = {
    "tier_1_always_fetch": [
        "fred", "gdelt", "newsapi", "worldbank", "finnhub"
    ],
    "tier_2_by_domain": {
        "energy":      ["eia", "open_meteo", "acled"],
        "trade":       ["un_comtrade", "wto", "finnhub_forex"],
        "labour":      ["bls_jolts", "ilo", "layoffs_fyi"],
        "geopolitics": ["acled", "ucdp", "gdelt_events"],
        "climate":     ["noaa", "nasa_earth", "open_meteo"],
        "social":      ["reddit", "google_trends", "wikipedia_pageviews"],
        "health":      ["who", "our_world_in_data", "cdc"]
    },
    "tier_3_always_available": [
        "rest_countries", "geonames", "dbnomics"
    ]
}
```

All fetches have a 10-second timeout. Failed fetches are logged but never block the pipeline. When data is missing, agents lower their confidence scores automatically.

---

## 15. LLM Strategy — Near Zero Cost

### Assignment by agent type

| Agent | LLM | Reason |
|---|---|---|
| Orchestrator | Claude Haiku | Needs reliable structured JSON output |
| Scout | No LLM — pure Python | Just API calls and formatting |
| Knowledge Graph | No LLM — NetworkX query | Graph traversal, not language |
| Domain agents (all 23) | Groq — Llama 3.3 70B | Fast · free · excellent for domain analysis |
| Debate Moderator | Groq | Structured comparison task |
| Historian | Groq | Pattern matching + structured output |
| Scenario Builder | Claude Haiku | Branching logic needs reliability |
| Counterfactual | Groq | Structured what-if analysis |
| Watchdog | Groq | Fact-checking against data |
| Confidence Rater | Groq | Scoring task |
| Bias Checker | Groq | Structured audit |
| Connector | Claude Haiku | Finding cross-domain links — needs quality |
| Personaliser | Claude Haiku | Nuanced personal impact writing |
| Summariser | Groq | Summary is a well-defined task |
| Prediction Logger | No LLM — pure Python | Just structured data storage |

### Cost per query

```
Complex query (20 agents):

  Orchestrator:     ~500 tokens  × Claude Haiku  = ~$0.0003
  20 domain agents: ~800 tokens  × Groq (free)   = $0.00
  Scenario Builder: ~600 tokens  × Claude Haiku  = ~$0.0004
  Connector:        ~1000 tokens × Claude Haiku  = ~$0.0006
  Personaliser:     ~600 tokens  × Claude Haiku  = ~$0.0004
  All other agents: ~2000 tokens × Groq (free)   = $0.00
                                           Total ≈ $0.0017

1,000 queries/month  ≈  $1.70
10,000 queries/month ≈  $17.00
100,000 queries/month ≈ $170.00
```

### Fallback chain

```
Claude Haiku → NVIDIA NIM (free, 40 RPM) → Gemini Flash (free, 250/day) → Groq
```

```python
async def call_with_fallback(prompt: str, tier: str) -> str:
    providers = {
        "quality": [claude_haiku, nvidia_nim, gemini_flash, groq],
        "fast":    [groq, nvidia_nim, gemini_flash, claude_haiku]
    }
    for provider in providers[tier]:
        try:
            return await provider.complete(prompt, timeout=15)
        except (RateLimitError, TimeoutError, APIError) as e:
            log_fallback(provider.name, str(e))
            continue
    raise AllProvidersFailedError()
```

### Fully free mode

```bash
# Set in .env
ANTHROPIC_API_KEY=none

# System uses Groq for everything
# Quality slightly lower — still very good
# Cost: $0.00
```

---

## 16. Trust Layer — Source Citation + Confidence

Every single ripple claim in the chain shows:

```python
@dataclass
class CitedClaim:
    claim: str                          # the statement
    confidence: float                   # 0.0–1.0
    confidence_color: str               # green | amber | red
    sources: List[Source]               # what backs this up
    data_points: List[str]              # specific figures
    uncertainty_note: str               # what would change this
    contradicting_view: str             # the other side
    timestamp: datetime                 # when this was generated
    staleness_hours: int                # how old the source data is

@dataclass
class Source:
    name: str                           # "FRED", "GDELT", "Finnhub"
    url: str                            # direct link to the data
    last_updated: datetime              # when this source last updated
    reliability_score: float            # pre-rated 0–1
```

### UI implementation

On hover over any ripple claim, a tooltip shows:
- Which data sources support it
- The specific data points cited
- When the data was last updated
- The contradicting view (if any)
- The confidence score with explanation

Color coding:
```
Green  (>0.80) → Strong data support
Amber  (0.60–0.80) → Moderate support, some uncertainty
Red    (<0.60) → Weak support — treat with caution
```

A staleness warning appears if source data is more than 24 hours old.

### Bias checker output

The Bias Checker flags systematic gaps in data coverage:

```
⚠ Data coverage note: This analysis draws primarily from US, EU, and UK sources.
  Coverage for Southeast Asia, Africa, and Latin America is limited.
  The impact on those regions may be underestimated.
```

---

## 17. The Feedback Loop — Prediction Tracking

This is the most important long-term feature. It is what turns Cascade from a demo into a credible system.

### How it works

Every verifiable claim Cascade makes is logged with a timestamp:

```python
@dataclass
class PredictionLog:
    id: str                             # UUID
    claim: str                          # "Canadian tech hiring will slow 10–15% within 6 months"
    domain: str                         # "labour"
    direction: str                      # "increase" | "decrease" | "stable"
    magnitude: str                      # "10–15%"
    timeframe_days: int                 # 180 (6 months)
    confidence: float                   # 0.74
    generated_at: datetime
    verification_date: datetime         # generated_at + timeframe_days
    status: str                         # "pending" | "correct" | "incorrect" | "partial"
    verification_source: str            # which data source confirmed/denied
    actual_outcome: str                 # what actually happened
```

### Verification process

A background job runs daily. For every prediction whose `verification_date` has passed, it:

1. Fetches current data from the relevant source
2. Compares to the original prediction direction and magnitude
3. Marks as `correct`, `incorrect`, or `partial`
4. Updates the running accuracy score

```python
async def verify_predictions():
    due = get_predictions_due_for_verification()
    for prediction in due:
        actual_data = await fetch_verification_data(
            prediction.domain,
            prediction.timeframe_days
        )
        outcome = compare_prediction_to_reality(prediction, actual_data)
        update_prediction_log(prediction.id, outcome)
        update_accuracy_score(prediction.domain, outcome)
```

### Public accuracy dashboard

A live page shows:

```
Cascade Accuracy Score — Updated daily

Overall:          71% correct (last 90 days)
Labour domain:    76% correct
Energy domain:    69% correct
Inflation domain: 74% correct
Geopolitics:      58% correct (inherently harder)

Based on 847 verified predictions since launch.
Methodology: [link]
```

This becomes the entire moat. Nobody else has this. It is what gets you press coverage, user trust, and funding conversations.

---

## 18. Error Handling + Edge Cases

### Query-level

| Scenario | Response |
|---|---|
| Too vague ("tell me about the world") | Ask 1 clarifying question |
| Not a world event query | Polite redirect with example queries |
| Query in another language | Process and respond in same language |
| Query >500 words | Truncate to 500, notify user |
| Offensive or harmful content | Block before orchestrator, standard message |
| Very recent event (<2 hours old) | Process but flag: "Limited data — very recent event" |
| Obscure regional event with no data | Process on LLM knowledge, heavy uncertainty caveat |

### Agent-level

| Scenario | Response |
|---|---|
| Agent times out (>20 seconds) | Marked "timed out" in UI, chain continues |
| Agent returns malformed JSON | Output discarded, gap noted in chain |
| Two agents directly contradict | Debate round triggered automatically |
| All agents time out | Retry with simpler manifest |
| Groq rate limit | Switch to NVIDIA NIM silently |
| Claude rate limit | Switch to Groq for that call |
| All LLMs fail | Return last cached result for similar query + warning |

### Data-level

| Scenario | Response |
|---|---|
| FRED API down | Proceed without, confidence capped at 0.6 |
| NewsAPI limit hit | Use cached headlines (max 1hr old) |
| GDELT timeout | Geopolitics agent notes uncertainty |
| All APIs fail | Proceed on LLM knowledge, large disclaimer shown |
| Stale data (>6hrs) | Yellow staleness warning on every affected claim |

### UI-level

| Scenario | Response |
|---|---|
| SSE drops mid-stream | Auto-reconnect in 3 seconds, resume from last event |
| User submits new query mid-stream | Cancel current stream cleanly, start new one |
| Browser tab backgrounded | Stream pauses, resumes on focus |
| Session expires | "Session expired" message, profile preserved |
| Slow connection (<1 Mbps) | Reduced streaming speed, no content loss |

---

## 19. Hallucination Guardrails — 3 Layers

**Layer 1 — Grounding prompt (in every agent)**

```
You MUST base your analysis on the provided data context.
If the data does not support a claim, say "uncertain" and
score confidence below 0.5.
Do NOT invent statistics, figures, or specific predictions.
Use hedged language: "likely" · "signals suggest" · "historically"
Never use: "will" · "definitely" · "certainly"
```

**Layer 2 — Watchdog agent**

Receives every agent output + the raw data context. Checks every factual claim:

```python
WATCHDOG_PROMPT = """
You are a fact-checker. Check every specific claim in these outputs
against the provided data. Return JSON flags for anything unsupported.

Flag types:
- UNSUPPORTED: No data source confirms this
- CONTRADICTED: Data source contradicts this
- STALE: Data is more than 24 hours old
- INVENTED: Specific figure appears made up
"""
```

Flagged claims are removed or marked with a red warning in the UI.

**Layer 3 — Confidence display + stuck loop detection**

```python
def detect_hallucination_patterns(agent_outputs: List[AgentOutput]) -> List[str]:
    flags = []
    # Stuck loop: agent repeating same output across retries
    if outputs_are_identical(agent_outputs):
        flags.append("STUCK_LOOP")
    # Contradiction: agent contradicts knowledge graph relationship
    for output in agent_outputs:
        if contradicts_knowledge_graph(output):
            flags.append(f"CONTRADICTS_KG: {output.domain}")
    # Low confidence + high severity = extra warning
    for output in agent_outputs:
        if output.confidence < 0.5 and output.severity == "critical":
            flags.append(f"UNCONFIDENT_CRITICAL: {output.domain}")
    return flags
```

---

## 20. Human Notification System

For the hosted demo, alerts fire when:
- All LLM providers fail simultaneously
- Daily spend exceeds configured threshold
- A single query takes more than 5 minutes
- Error rate exceeds 20% in any 1-hour window

```
🚨 Cascade Alert

Event:    All LLM providers failed
Query:    "What does X mean for Y"
Time:     2026-03-20 14:32 UTC
Session:  abc-123

Last error: Claude rate limit, Groq 503, NVIDIA NIM timeout
Suggested fix: Wait 5 minutes and retry. Check API status pages.
```

Alerts sent via:
- Email (configurable SMTP — free)
- Slack webhook (optional)

---

## 21. Sharing + Virality Features

### Shareable links

Every completed analysis generates a unique shareable URL:

```
https://cascade.yourdomain.com/analysis/abc123xyz
```

The link renders a static snapshot of the analysis — all ripple chain, all scenarios, all sources — without requiring the viewer to run the query again. The viewer can then "Run fresh analysis" to update it.

### Social sharing cards

When a link is shared, Open Graph meta tags generate a preview card:

```html
<meta property="og:title"
      content="What the US-China trade war means for tech workers in Canada">
<meta property="og:description"
      content="Cascade found 14 ripple effects across 8 domains.
               Labour confidence: 74%. Best case: hiring stabilises in 9 months.">
<meta property="og:image" content="/og-image/abc123xyz">
```

The OG image is auto-generated as a clean visual summary of the top 5 ripples.

### Export

Users can export any analysis as:
- Markdown (`.md` file — clean, readable, shareable)
- PDF (generated server-side with WeasyPrint — free)
- JSON (full structured data — for developers)

---

## 22. Alert + Watchlist System

Users can save any query to their watchlist. Cascade re-runs the analysis automatically when significant new data arrives for that topic.

```python
@dataclass
class WatchlistEntry:
    query: str
    profile_snapshot: UserProfile       # profile at time of saving
    created_at: datetime
    last_run: datetime
    alert_threshold: float              # 0.0–1.0 — how much must change
    notification_channel: str          # "browser" | "email"

def check_watchlist():
    for entry in active_watchlist:
        if significant_new_data_available(entry.query):
            new_analysis = run_cascade(entry.query, entry.profile_snapshot)
            delta = compare_analyses(entry.last_analysis, new_analysis)
            if delta.magnitude > entry.alert_threshold:
                notify_user(entry, delta)
                entry.last_run = datetime.now()
```

What triggers an alert:
- A major new GDELT event in a tracked domain
- FRED data showing significant movement (>1 standard deviation)
- New news articles with high relevance score
- A watchlisted scenario shifting from base to worst case probability

---

## 23. Comparison Mode

The user can compare two events side by side:

```
Event A: 2008 Financial Crisis
Event B: 2025 AI-Driven Recession

Side-by-side ripple chains showing:
  - Where they diverge
  - Where they converge
  - What the 2008 crisis predicts about 2025
  - What is genuinely different this time
```

Two full agent pipelines run in parallel. The Connector then runs a third time in comparison mode, finding similarities and differences between the two chains.

---

## 24. Tech Stack

| Layer | Tool | Cost |
|---|---|---|
| Backend framework | FastAPI (Python) | Free |
| Agent orchestration | LangGraph + LangChain | Free |
| Streaming | Server-Sent Events | Free — built into HTTP |
| Knowledge graph | NetworkX | Free |
| Prediction storage | SQLite (local) | Free |
| Session storage | Python in-memory | Free |
| Profile storage | Browser localStorage | Free |
| Primary LLM | Claude Haiku | ~$0.0017/query |
| Secondary LLM | Groq Llama 3.3 70B | Free |
| Fallback LLM 1 | NVIDIA NIM | Free — 40 RPM |
| Fallback LLM 2 | Google Gemini Flash | Free — 250/day |
| Data sources | 40+ free APIs | Free |
| PDF export | WeasyPrint | Free |
| Rate limiting | slowapi | Free |
| Frontend | Vanilla HTML + CSS + JS | Free |
| Version control | Git + GitHub | Free |

**No database server. No Docker required. No cloud account needed. Runs on any laptop.**

---

## 25. Project Folder Structure

```
cascade/
│
├── main.py                         # FastAPI entry point
├── config.py                       # All settings — models, thresholds, limits
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── graph/
│   ├── pipeline.py                 # LangGraph StateGraph
│   ├── state.py                    # CascadeState TypedDict
│   └── routers.py                  # Conditional edge logic
│
├── agents/
│   ├── base_agent.py               # Base: retry, fallback, confidence
│   ├── orchestrator.py             # Complexity scoring + agent manifest
│   ├── scout.py                    # Parallel data fetcher
│   ├── knowledge_graph_agent.py    # Queries NetworkX graph
│   ├── connector.py                # Builds ripple chain
│   ├── debate_moderator.py         # Surfaces + resolves conflicts
│   ├── historian.py                # Finds historical parallels
│   ├── scenario_builder.py         # Best / base / worst branches
│   ├── counterfactual.py           # What-if analysis
│   ├── watchdog.py                 # Hallucination detection
│   ├── confidence_rater.py         # Claim scoring
│   ├── bias_checker.py             # Data coverage audit
│   ├── personaliser.py             # User profile application
│   ├── summariser.py               # Final summary
│   ├── prediction_logger.py        # Logs verifiable claims
│   │
│   └── domain/                     # 23 conditional agents
│       ├── energy.py
│       ├── trade.py
│       ├── labour.py
│       ├── inflation.py
│       ├── geopolitics.py
│       ├── currency.py
│       ├── supply_chain.py
│       ├── technology.py
│       ├── housing.py
│       ├── healthcare.py
│       ├── climate.py
│       ├── food.py
│       ├── finance.py
│       ├── migration.py
│       ├── social.py
│       ├── mental_health.py
│       ├── education.py
│       ├── crime_safety.py
│       ├── debt_credit.py
│       ├── media_information.py
│       ├── demographics.py
│       ├── infrastructure.py
│       └── religion_culture.py
│
├── data/
│   ├── fetchers/
│   │   ├── fred.py
│   │   ├── worldbank.py
│   │   ├── gdelt.py
│   │   ├── finnhub.py
│   │   ├── newsapi.py
│   │   ├── reddit.py
│   │   ├── google_trends.py
│   │   ├── acled.py
│   │   ├── bls.py
│   │   ├── un_comtrade.py
│   │   ├── open_meteo.py
│   │   ├── our_world_in_data.py
│   │   ├── wikipedia_pageviews.py
│   │   ├── guardian.py
│   │   ├── nytimes.py
│   │   └── rss_feeds.py
│   ├── cache.py                    # TTL-based in-memory cache
│   └── context_builder.py          # Assembles fetched data
│
├── knowledge/
│   ├── graph.py                    # NetworkX graph + query API
│   ├── relationships.py            # Causal relationship definitions
│   ├── country_sensitivities.py    # Per-country domain weights
│   └── historical_events.py        # ~200 major historical events DB
│
├── llm/
│   ├── providers.py                # Claude, Groq, NVIDIA, Gemini wrappers
│   ├── fallback.py                 # Fallback chain logic
│   └── token_counter.py            # Daily spend tracker
│
├── streaming/
│   └── sse.py                      # SSE event builder
│
├── trust/
│   ├── citation.py                 # Source attribution system
│   ├── confidence.py               # Scoring + colour coding
│   └── bias_detector.py            # Coverage gap detection
│
├── predictions/
│   ├── logger.py                   # Log claims to SQLite
│   ├── verifier.py                 # Daily verification job
│   └── accuracy.py                 # Running accuracy scores
│
├── sharing/
│   ├── snapshots.py                # Generate shareable links
│   ├── og_cards.py                 # Open Graph card generation
│   └── export.py                   # PDF / Markdown / JSON export
│
├── watchlist/
│   ├── manager.py                  # Watchlist CRUD
│   └── checker.py                  # Background job — check for updates
│
├── session/
│   └── manager.py                  # In-memory session store (TTL 2hrs)
│
├── safety/
│   ├── input_filter.py             # Query validation + content filter
│   └── output_filter.py            # Output safety checks
│
└── frontend/
    ├── index.html                  # Single-file UI
    ├── style.css
    └── cascade.js                  # SSE listener + DOM rendering
```

---

## 26. Running Locally

### Requirements

- Python 3.11+
- No GPU needed
- No Docker needed
- Any OS

### Setup

```bash
git clone https://github.com/yourusername/cascade.git
cd cascade
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python main.py
# Open http://localhost:8000
```

### .env template

```bash
# Required for quality mode
ANTHROPIC_API_KEY=your_key_here

# Free — required
GROQ_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
GUARDIAN_API_KEY=your_key_here
NYTIMES_API_KEY=your_key_here

# Free — optional fallbacks
NVIDIA_NIM_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
ALPHA_VANTAGE_KEY=your_key_here
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here

# Settings
MAX_AGENTS=33
SESSION_TTL_HOURS=2
ENABLE_CONTENT_FILTER=true
DAILY_BUDGET_USD=2.00
MAX_COMPLEXITY_OVERRIDE=5.0    # lower to reduce cost
PREDICTION_LOG_PATH=./data/predictions.db
```

### Fully free mode (zero cost)

```bash
ANTHROPIC_API_KEY=none python main.py
```

Uses Groq for all agents. Excellent quality. Zero cost.

---

## 27. How Others Can Use This

### Option A — Clone + run (recommended)

```bash
git clone https://github.com/yourusername/cascade.git
cd cascade
cp .env.example .env
# Add YOUR OWN keys — never use someone else's
python main.py
```

Each person uses their own API keys. Your keys never leave your machine.

### Option B — Fork + customise

Fork on GitHub. Add new domain agents, change the knowledge graph, customise the UI. Each new domain agent is one Python file. Adding a new data source is one fetcher file. The system is designed to be modular.

### Option C — Hosted demo (your server)

You deploy at `cascade.yourdomain.com` with your keys and rate limits:
- 3 queries per IP per day on the free tier
- Query length capped at 300 characters
- Daily spend cap enforced in code

Free hosting options: Railway ($5/month) · Fly.io (free tier) · Render (free tier)

---

## 28. Protecting Your API Keys

```
RULE 1: .env is in .gitignore — verify before every commit
RULE 2: Never hardcode keys in any Python file
RULE 3: Never expose keys in JavaScript — all LLM calls via backend
RULE 4: Set monthly spend limits in Anthropic console
RULE 5: Rate limit your public demo endpoint
```

```python
# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.get("/cascade/stream")
@limiter.limit("3/day")
async def cascade_stream(request: Request, query: str):
    ...
```

---

## 29. Cost Management

### Built-in safeguards

**Token budget per agent**
```python
MAX_TOKENS = {
    "orchestrator": 500,
    "domain_agent": 800,
    "connector": 1200,
    "personaliser": 600,
    "scenario_builder": 800,
    "summariser": 400
}
```

**Daily spend cap**
```python
if daily_token_tracker.get_usd_today() > DAILY_BUDGET_USD:
    llm_config.force_free_tier = True
    # All calls route to Groq/NVIDIA NIM until midnight UTC
```

**Query result caching**
Top 100 common query patterns cached for 1 hour. Second user asking the same thing costs zero.

**Complexity cap**
```python
MAX_COMPLEXITY_OVERRIDE = 4.0  # in config.py
# Caps at 17–22 agents regardless of query
# Reduces average cost by ~30%
```

**Pre-computation**
Every hour, the system pre-computes analyses for the top 20 trending GDELT events. These load instantly at zero incremental cost.

---

## 30. Pre-flight Checklist

- [ ] Python 3.11+ installed
- [ ] `pip install -r requirements.txt` completed
- [ ] `.env` created from `.env.example`
- [ ] Anthropic API key added (console.anthropic.com)
- [ ] Groq API key added (console.groq.com — free)
- [ ] Finnhub key added (finnhub.io — free)
- [ ] NewsAPI key added (newsapi.org — free)
- [ ] Guardian key added (open-platform.theguardian.com — free)
- [ ] `.env` confirmed in `.gitignore`
- [ ] Monthly spend limit set in Anthropic console
- [ ] `python main.py` runs without errors
- [ ] Browser opens `localhost:8000`
- [ ] Test query submitted and all phases stream correctly
- [ ] Shareable link generates after completion
- [ ] Prediction log confirms claims are being stored
- [ ] Knowledge graph loads and queries correctly

---

## Accuracy Promise

Cascade logs every verifiable prediction it makes. A daily background job checks outcomes against real data. Accuracy scores are published live. This is not a claim — it is a commitment built into the architecture from day one.

---

## Contributing

Every new domain agent is a single Python file. Every new data source is a single fetcher file. If you build something useful, open a PR. The most valuable contributions are: new historical events in the database, new knowledge graph relationships, new data fetchers for non-English sources, and improvements to the prediction verification logic.

---

## License

MIT

---

*Built with LangGraph · LangChain · Claude · Groq · FastAPI · FRED · GDELT · Finnhub · NewsAPI · World Bank · NetworkX · SQLite*