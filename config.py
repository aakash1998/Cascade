"""
config.py — Central configuration for Cascade
================================================
This is the single source of truth for every setting in the app.
Every other file imports from here — nothing reads .env directly.

How it works:
  1. Loads your .env file automatically on import
  2. Reads every environment variable with a safe default
  3. Validates that the minimum required keys are present
  4. Exposes clean Python objects that the rest of the app uses

Usage:
  from config import settings
  print(settings.ANTHROPIC_API_KEY)
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file from the project root
# This must happen before any other imports that need env vars
load_dotenv()


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def _get(key: str, default: str = "") -> str:
    """Read an env variable. Returns default if not set or empty."""
    return os.getenv(key, default).strip()

def _get_bool(key: str, default: bool = False) -> bool:
    """Read a boolean env variable. Accepts true/false/1/0."""
    val = os.getenv(key, str(default)).strip().lower()
    return val in ("true", "1", "yes")

def _get_int(key: str, default: int = 0) -> int:
    """Read an integer env variable. Returns default if not set."""
    try:
        return int(os.getenv(key, str(default)).strip())
    except ValueError:
        return default

def _get_float(key: str, default: float = 0.0) -> float:
    """Read a float env variable. Returns default if not set."""
    try:
        return float(os.getenv(key, str(default)).strip())
    except ValueError:
        return default


# ─────────────────────────────────────────────
# SETTINGS DATACLASS
# ─────────────────────────────────────────────

@dataclass
class Settings:
    """
    All settings for Cascade in one place.
    Grouped by category for easy navigation.
    """

    # ── LLM PROVIDERS ─────────────────────────────────────
    # These are the AI brains. Claude for critical reasoning,
    # Groq for fast free domain agents.

    ANTHROPIC_API_KEY: str = field(default_factory=lambda: _get("ANTHROPIC_API_KEY"))
    GROQ_API_KEY: str      = field(default_factory=lambda: _get("GROQ_API_KEY"))
    NVIDIA_NIM_API_KEY: str = field(default_factory=lambda: _get("NVIDIA_NIM_API_KEY"))
    GOOGLE_API_KEY: str    = field(default_factory=lambda: _get("GOOGLE_API_KEY"))

    # Which model to use for each agent tier
    # Tier 1 = critical reasoning (orchestrator, connector, personaliser)
    # Tier 2 = domain analysis (all 23 domain agents — uses Groq free)
    LLM_TIER1_MODEL: str = "claude-haiku-4-5"
    LLM_TIER2_MODEL: str = "llama-3.3-70b-versatile"  # Groq model name

    # Fallback order when a provider fails or hits rate limits
    # The system tries each in order until one works
    LLM_FALLBACK_ORDER: list = field(default_factory=lambda: [
        "anthropic",   # primary
        "groq",        # first fallback — free
        "nvidia_nim",  # second fallback — free 40 RPM
        "gemini"       # last resort — free 250/day
    ])

    # ── DATA + SEARCH ─────────────────────────────────────
    # Tavily replaces 15+ individual news APIs with one search tool.
    # Finnhub provides structured financial/market data.
    # FRED provides economic indicators (no key needed).

    TAVILY_API_KEY: str    = field(default_factory=lambda: _get("TAVILY_API_KEY"))
    FINNHUB_API_KEY: str   = field(default_factory=lambda: _get("FINNHUB_API_KEY"))
    FRED_API_KEY: str      = field(default_factory=lambda: _get("FRED_API_KEY"))
    ALPHA_VANTAGE_KEY: str = field(default_factory=lambda: _get("ALPHA_VANTAGE_KEY"))
    NEWS_API_KEY: str = field(default_factory=lambda: _get("NEWS_API_KEY"))
    # These sources need no API key — always enabled
    WORLD_BANK_ENABLED: bool  = True
    GDELT_ENABLED: bool       = True
    OPEN_METEO_ENABLED: bool  = True
    REST_COUNTRIES_ENABLED: bool = True

    # How many search results Tavily returns per agent call
    # Higher = richer context but slower and more tokens
    TAVILY_MAX_RESULTS: int = 5

    # How long to cache data fetches (seconds)
    # Prevents hammering the same API twice in one session
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # HTTP timeout for all external API calls (seconds)
    # If an API doesn't respond in time, it's skipped gracefully
    API_TIMEOUT_SECONDS: int = 10

    # ── AGENT SETTINGS ────────────────────────────────────
    # Controls how many agents spin up and how they behave.

    # Hard cap on total agents per query (permanent + conditional)
    MAX_AGENTS: int = field(default_factory=lambda: _get_int("MAX_AGENTS", 33))

    # Complexity score cap (1.0 - 5.0)
    # Lower this to reduce cost: 3.0 = max ~16 agents instead of 33
    MAX_COMPLEXITY: float = field(default_factory=lambda: _get_float("MAX_COMPLEXITY_OVERRIDE", 5.0))

    # How long each agent has to respond before being skipped
    # Skipped agents are marked "timed out" in the UI — pipeline continues
    AGENT_TIMEOUT_SECONDS: int = 20

    # How many times an agent retries before asking for peer review
    AGENT_RETRY_BUDGET: int = 3

    # Confidence score below which hallucination flag is triggered
    # Scale 0.0 - 1.0. Below this = agent output is flagged + reviewed
    HALLUCINATION_CONFIDENCE_THRESHOLD: float = 0.6

    # Max tokens each agent type can generate
    # Keeps costs predictable and responses focused
    MAX_TOKENS: dict = field(default_factory=lambda: {
        "orchestrator":    600,
        "domain_agent":    800,
        "connector":      1200,
        "debate":          400,
        "historian":       600,
        "scenario":        800,
        "counterfactual":  600,
        "personaliser":    700,
        "summariser":      400,
        "watchdog":        400,
    })

    # ── SESSION + MEMORY ──────────────────────────────────
    # Controls how conversation history is stored and managed.
    # Currently in-memory (RAM). Will swap to Azure SQL later.

    SESSION_TTL_HOURS: int = field(default_factory=lambda: _get_int("SESSION_TTL_HOURS", 2))
    MAX_CONVERSATION_TURNS: int = field(default_factory=lambda: _get_int("MAX_CONVERSATION_TURNS", 10))

    # ── COST MANAGEMENT ───────────────────────────────────
    # Daily budget cap in USD.
    # When hit, all LLM calls switch to free providers automatically.

    DAILY_BUDGET_USD: float = field(default_factory=lambda: _get_float("DAILY_BUDGET_USD", 2.00))

    # ── STORAGE — LOCAL (Phase 1) ─────────────────────────
    # Using local filesystem and SQLite for now.
    # These paths get swapped out for Azure Blob + Azure SQL later.

    # Where raw data files are saved
    DATA_DIR: str = "./data"

    # Where user session snapshots are saved (for shareable links)
    SNAPSHOTS_DIR: str = "./data/snapshots"

    # SQLite database for prediction logging and verification
    PREDICTION_DB_PATH: str = field(
        default_factory=lambda: _get("PREDICTION_DB_PATH", "./data/predictions.db")
    )

    # ── SAFETY + RATE LIMITING ────────────────────────────
    # Content filter blocks harmful queries before they reach agents.
    # Rate limit protects your API keys on the public demo.

    ENABLE_CONTENT_FILTER: bool = field(
        default_factory=lambda: _get_bool("ENABLE_CONTENT_FILTER", True)
    )

    # Max queries per IP per day (for hosted demo only)
    RATE_LIMIT_PER_IP_PER_DAY: int = field(
        default_factory=lambda: _get_int("RATE_LIMIT_PER_IP_PER_DAY", 3)
    )

    # ── OBSERVABILITY ─────────────────────────────────────
    # LangSmith traces every agent call — inputs, outputs, latency, cost.
    # Optional but highly recommended for debugging.

    LANGSMITH_API_KEY: str = field(default_factory=lambda: _get("LANGSMITH_API_KEY"))
    LANGSMITH_PROJECT: str = field(
        default_factory=lambda: _get("LANGSMITH_PROJECT", "cascade-ripple-engine")
    )

    # ── DEBUG ─────────────────────────────────────────────
    # When True: prints every agent prompt + response to console.
    # Turn off in production — very noisy.

    DEBUG_AGENTS: bool = field(default_factory=lambda: _get_bool("DEBUG_AGENTS", False))

    # When True: skips real API calls, returns mock data instantly.
    # Use this to test the UI and pipeline flow without spending tokens.
    LOCAL_DEV_MODE: bool = field(default_factory=lambda: _get_bool("LOCAL_DEV_MODE", False))

    # When True: forces all LLM calls to free providers (Groq/NVIDIA/Gemini).
    # Useful when you want to test without spending Anthropic credits.
    FREE_MODE_ONLY: bool = field(default_factory=lambda: _get_bool("FREE_MODE_ONLY", False))


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def _validate(s: Settings) -> None:
    """
    Check that the minimum required keys are present.
    Raises a clear error message telling you exactly what's missing.
    Called once at startup — fails fast before any agent runs.
    """
    errors = []

    if not s.GROQ_API_KEY:
        errors.append("  GROQ_API_KEY is missing — get it free at console.groq.com")

    if not s.TAVILY_API_KEY:
        errors.append("  TAVILY_API_KEY is missing — get it free at app.tavily.com")

    if not s.FINNHUB_API_KEY:
        errors.append("  FINNHUB_API_KEY is missing — get it free at finnhub.io")

    # Anthropic is optional — app runs in free mode without it
    if not s.ANTHROPIC_API_KEY or s.ANTHROPIC_API_KEY == "your_key_here":
        print("⚠️  Warning: ANTHROPIC_API_KEY not set — running in free mode (Groq only)")
        print("   Quality will be slightly lower. Set key for best results.\n")

    if errors:
        print("\n❌ Cascade cannot start — missing required API keys:\n")
        for e in errors:
            print(e)
        print("\nAdd them to your .env file and restart.\n")
        raise SystemExit(1)


# ─────────────────────────────────────────────
# CREATE REQUIRED DIRECTORIES
# ─────────────────────────────────────────────

def _create_dirs(s: Settings) -> None:
    """
    Create local storage directories if they don't exist yet.
    Runs at startup — safe to call multiple times.
    """
    dirs = [
        s.DATA_DIR,
        s.SNAPSHOTS_DIR,
        "./data/fetchers",
        "./logs",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

# This is the single object every other file imports.
# It is created once when config.py is first imported.
settings = Settings()

# Run validation and setup immediately on import
_validate(settings)
_create_dirs(settings)

# Set LangSmith env vars if key is provided
# LangGraph reads these automatically — no other setup needed
if settings.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]    = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"]    = settings.LANGSMITH_PROJECT


# ─────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run this file directly to verify your config is working:
      python config.py
    """
    print("✅ Config loaded successfully\n")
    print(f"  Groq key present:     {'✅' if settings.GROQ_API_KEY else '❌'}")
    print(f"  Anthropic key present: {'✅' if settings.ANTHROPIC_API_KEY else '⚠️  (free mode)'}")
    print(f"  Tavily key present:    {'✅' if settings.TAVILY_API_KEY else '❌'}")
    print(f"  Finnhub key present:   {'✅' if settings.FINNHUB_API_KEY else '❌'}")
    print(f"  LangSmith enabled:     {'✅' if settings.LANGSMITH_API_KEY else '⚠️  (optional)'}")
    print(f"\n  Max agents:    {settings.MAX_AGENTS}")
    print(f"  Daily budget:  ${settings.DAILY_BUDGET_USD}")
    print(f"  Debug mode:    {settings.DEBUG_AGENTS}")
    print(f"  Free mode:     {settings.FREE_MODE_ONLY}")
    print(f"  Local dev:     {settings.LOCAL_DEV_MODE}")
    print(f"\n  Data dir:      {settings.DATA_DIR}")
    print(f"  Predictions:   {settings.PREDICTION_DB_PATH}")