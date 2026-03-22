"""
llm/providers.py — LLM provider wrappers + fallback chain
==========================================================
This file is the brain connector. It wraps Claude, Groq, NVIDIA NIM,
and Gemini into one clean interface so the rest of the app never
has to worry about which LLM is being used.

How the fallback chain works:
  Every LLM call goes through call_llm().
  If Claude fails (rate limit, timeout, API error) →
    it automatically tries Groq (free) →
      then NVIDIA NIM (free) →
        then Gemini Flash (free)

  The agent that made the call never knows a fallback happened.
  It just gets a response.

Two tiers of models:
  Tier 1 (quality) — Claude Haiku
    Used by: Orchestrator, Connector, Personaliser, Scenario Builder
    Why: These agents need reliable structured JSON and nuanced reasoning

  Tier 2 (fast + free) — Groq Llama 3.3 70B
    Used by: All 23 domain agents, Watchdog, Summariser, Debate
    Why: Fast, free, excellent for focused domain analysis

Usage:
  from llm.providers import call_llm, call_llm_stream

  # Single response
  response = await call_llm(
      prompt="Analyse the impact of X on energy markets",
      tier="tier2",           # "tier1" or "tier2"
      max_tokens=800,
      system="You are an energy market analyst..."
  )

  # Streaming response (token by token)
  async for token in call_llm_stream(prompt=..., tier="tier1"):
      print(token, end="", flush=True)
"""

import os
import json
import asyncio
from typing import AsyncGenerator, Optional

from config import settings


# ─────────────────────────────────────────────
# DAILY SPEND TRACKER
# ─────────────────────────────────────────────

class DailySpendTracker:
    """
    Tracks estimated daily token spend across all LLM calls.
    When the daily budget is hit, all calls are routed to
    free providers automatically.

    Cost estimates (approximate, as of 2025):
      Claude Haiku:  $0.0025 per 1k input tokens
                     $0.0125 per 1k output tokens
      Groq:          $0.00 (free tier)
      NVIDIA NIM:    $0.00 (free tier)
      Gemini Flash:  $0.00 (free tier, 250 req/day)
    """

    def __init__(self):
        self.total_usd_today = 0.0
        self.total_tokens_today = 0
        self.call_count = 0
        self._date = self._today()

    def _today(self) -> str:
        from datetime import date
        return date.today().isoformat()

    def _reset_if_new_day(self):
        """Resets counters at midnight."""
        if self._today() != self._date:
            self.total_usd_today = 0.0
            self.total_tokens_today = 0
            self.call_count = 0
            self._date = self._today()

    def add(self, provider: str, input_tokens: int, output_tokens: int):
        """
        Records a completed LLM call and updates spend estimate.
        Called after every successful LLM response.
        """
        self._reset_if_new_day()

        # Cost per 1k tokens by provider
        costs = {
            "anthropic": {"input": 0.0025, "output": 0.0125},
            "groq":      {"input": 0.0,    "output": 0.0},
            "nvidia_nim":{"input": 0.0,    "output": 0.0},
            "gemini":    {"input": 0.0,    "output": 0.0},
        }

        if provider in costs:
            cost = (
                (input_tokens  / 1000) * costs[provider]["input"] +
                (output_tokens / 1000) * costs[provider]["output"]
            )
            self.total_usd_today += cost
            self.total_tokens_today += input_tokens + output_tokens
            self.call_count += 1

    def is_over_budget(self) -> bool:
        """Returns True if daily spend has exceeded the configured limit."""
        self._reset_if_new_day()
        return self.total_usd_today >= settings.DAILY_BUDGET_USD

    def summary(self) -> dict:
        """Returns current spend stats — shown in /health endpoint."""
        self._reset_if_new_day()
        return {
            "usd_today":    round(self.total_usd_today, 4),
            "budget_usd":   settings.DAILY_BUDGET_USD,
            "tokens_today": self.total_tokens_today,
            "calls_today":  self.call_count,
            "over_budget":  self.is_over_budget(),
        }


# Global spend tracker — one instance shared across all calls
spend_tracker = DailySpendTracker()


# ─────────────────────────────────────────────
# PROVIDER: ANTHROPIC (CLAUDE)
# ─────────────────────────────────────────────

async def _call_anthropic(
    prompt: str,
    system: str,
    max_tokens: int,
) -> str:
    """
    Calls Claude Haiku via the Anthropic API.
    Used for Tier 1 agents that need quality reasoning.

    Returns the response text as a string.
    Raises an exception if the call fails — caller handles fallback.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key not set")

    # Import here to avoid import errors if anthropic isn't installed
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = await client.messages.create(
        model=settings.LLM_TIER1_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    # Track spend
    spend_tracker.add(
        provider="anthropic",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

    return response.content[0].text


async def _stream_anthropic(
    prompt: str,
    system: str,
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    """
    Streams Claude's response token by token.
    Used when we want to show the analysis building in real time.
    Yields each text chunk as it arrives.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key not set")

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async with client.messages.stream(
        model=settings.LLM_TIER1_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


# ─────────────────────────────────────────────
# PROVIDER: GROQ
# ─────────────────────────────────────────────

async def _call_groq(
    prompt: str,
    system: str,
    max_tokens: int,
) -> str:
    """
    Calls Groq's Llama 3.3 70B model.
    Free tier — used for all 23 domain agents.
    Very fast — typically responds in under 2 seconds.

    Returns the response text as a string.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("Groq API key not set")

    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    response = await client.chat.completions.create(
        model=settings.LLM_TIER2_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system",  "content": system},
            {"role": "user",    "content": prompt},
        ],
    )

    # Track spend (Groq is free — just tracking token count)
    spend_tracker.add(
        provider="groq",
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
    )

    return response.choices[0].message.content


async def _stream_groq(
    prompt: str,
    system: str,
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    """
    Streams Groq's response token by token.
    Free and fast — good first choice for streaming domain agent outputs.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("Groq API key not set")

    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    stream = await client.chat.completions.create(
        model=settings.LLM_TIER2_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ─────────────────────────────────────────────
# PROVIDER: NVIDIA NIM
# ─────────────────────────────────────────────

async def _call_nvidia_nim(
    prompt: str,
    system: str,
    max_tokens: int,
) -> str:
    """
    Calls NVIDIA NIM via their OpenAI-compatible API.
    Free tier — 40 requests per minute.
    Used as second fallback when both Claude and Groq fail.

    NVIDIA NIM hosts many open models — we use Llama 3.1 70B here.
    """
    if not settings.NVIDIA_NIM_API_KEY:
        raise ValueError("NVIDIA NIM API key not set")

    import httpx

    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model": "meta/llama-3.1-70b-instruct",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
        response = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    spend_tracker.add(provider="nvidia_nim", input_tokens=0, output_tokens=0)
    return data["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────
# PROVIDER: GOOGLE GEMINI FLASH
# ─────────────────────────────────────────────

async def _call_gemini(
    prompt: str,
    system: str,
    max_tokens: int,
) -> str:
    """
    Calls Google Gemini Flash via their API.
    Free tier — 250 requests per day.
    Last resort fallback when all other providers fail.
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError("Google API key not set")

    import httpx

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={settings.GOOGLE_API_KEY}"
    )

    payload = {
        "contents": [{
            "parts": [{"text": f"{system}\n\n{prompt}"}]
        }],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }

    async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    spend_tracker.add(provider="gemini", input_tokens=0, output_tokens=0)
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ─────────────────────────────────────────────
# FALLBACK CHAIN — MAIN INTERFACE
# ─────────────────────────────────────────────

# Maps provider names to their async functions
PROVIDER_MAP = {
    "anthropic":  _call_anthropic,
    "groq":       _call_groq,
    "nvidia_nim": _call_nvidia_nim,
    "gemini":     _call_gemini,
}

STREAM_MAP = {
    "anthropic": _stream_anthropic,
    "groq":      _stream_groq,
}


def _get_provider_order(tier: str) -> list[str]:
    """
    Returns the ordered list of providers to try for a given tier.

    Tier 1 (quality): tries Claude first, falls back to others
    Tier 2 (fast):    tries Groq first (free), falls back to others

    If daily budget is exceeded or FREE_MODE_ONLY is set,
    Claude is skipped entirely — only free providers are used.
    """
    skip_paid = settings.FREE_MODE_ONLY or spend_tracker.is_over_budget()

    if tier == "tier1" and not skip_paid:
        return ["anthropic", "groq", "nvidia_nim", "gemini"]
    else:
        # Tier 2 or free mode — start with Groq
        return ["groq", "nvidia_nim", "gemini", "anthropic"]


async def call_llm(
    prompt:     str,
    tier:       str = "tier2",
    max_tokens: int = 800,
    system:     str = "You are a helpful analyst.",
) -> str:
    """
    The main LLM call function used by every agent.

    Tries providers in order based on tier. If one fails,
    automatically tries the next one. If all fail, raises
    a clear error.

    Args:
        prompt:     The user message / agent task
        tier:       "tier1" for quality (Claude first)
                    "tier2" for speed/free (Groq first)
        max_tokens: Max tokens in the response
        system:     The system prompt defining the agent's role

    Returns:
        The LLM response as a plain string

    Example:
        result = await call_llm(
            prompt="What is the impact of oil price rise on inflation?",
            tier="tier2",
            system="You are an expert inflation analyst.",
            max_tokens=600,
        )
    """
    providers = _get_provider_order(tier)
    last_error = None

    for provider in providers:
        if provider not in PROVIDER_MAP:
            continue

        try:
            if settings.DEBUG_AGENTS:
                print(f"🤖 Calling {provider} (tier={tier}, max_tokens={max_tokens})")

            result = await asyncio.wait_for(
                PROVIDER_MAP[provider](prompt, system, max_tokens),
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )

            if settings.DEBUG_AGENTS:
                print(f"✅ {provider} responded ({len(result)} chars)")

            return result

        except asyncio.TimeoutError:
            last_error = f"{provider} timed out after {settings.AGENT_TIMEOUT_SECONDS}s"
            print(f"⏱️  {last_error} — trying next provider")
            continue

        except Exception as e:
            last_error = f"{provider} failed: {str(e)}"
            print(f"⚠️  {last_error} — trying next provider")
            continue

    # All providers failed
    raise RuntimeError(
        f"All LLM providers failed. Last error: {last_error}\n"
        f"Providers tried: {providers}"
    )


async def call_llm_json(
    prompt:     str,
    tier:       str = "tier1",
    max_tokens: int = 600,
    system:     str = "You are a helpful analyst. Always respond with valid JSON only.",
) -> dict:
    """
    Like call_llm() but expects and parses a JSON response.
    Used by the Orchestrator and other agents that return structured data.

    Automatically retries once if JSON parsing fails —
    adding a stronger "respond with JSON only" instruction.

    Returns:
        Parsed dict from the LLM's JSON response

    Example:
        data = await call_llm_json(
            prompt="Return a JSON object with keys: score, domains",
            tier="tier1",
        )
        print(data["score"])  # 4.2
    """
    # First attempt
    raw = await call_llm(prompt, tier, max_tokens, system)

    try:
        # Strip markdown code blocks if the model wrapped JSON in ```
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json) and last line (```)
            cleaned = "\n".join(lines[1:-1])
        return json.loads(cleaned)

    except json.JSONDecodeError:
        # Second attempt with stronger JSON instruction
        strict_system = (
            system + "\n\nCRITICAL: Your response must be valid JSON and nothing else. "
            "No explanation, no markdown, no code blocks. Just the raw JSON object."
        )
        raw2 = await call_llm(prompt, tier, max_tokens, strict_system)

        try:
            cleaned2 = raw2.strip()
            if cleaned2.startswith("```"):
                lines = cleaned2.split("\n")
                cleaned2 = "\n".join(lines[1:-1])
            return json.loads(cleaned2)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON after 2 attempts.\n"
                f"Raw response: {raw2[:200]}...\n"
                f"Parse error: {e}"
            )


async def call_llm_stream(
    prompt:     str,
    tier:       str = "tier2",
    max_tokens: int = 800,
    system:     str = "You are a helpful analyst.",
) -> AsyncGenerator[str, None]:
    """
    Streaming version of call_llm().
    Yields text tokens as they arrive from the LLM.
    Used for the Connector, Personaliser, and Summariser
    so the frontend can show text building in real time.

    Falls back to non-streaming if the primary provider
    doesn't support streaming (NVIDIA NIM, Gemini).

    Example:
        async for token in call_llm_stream(prompt=..., tier="tier1"):
            yield { "data": json.dumps({"type": "chain_token", "token": token}) }
    """
    providers = _get_provider_order(tier)

    for provider in providers:
        # Only try streaming if this provider supports it
        if provider not in STREAM_MAP:
            # Try non-streaming fallback
            try:
                result = await call_llm(prompt, tier, max_tokens, system)
                # Simulate streaming by yielding the full response at once
                yield result
                return
            except Exception:
                continue

        try:
            if settings.DEBUG_AGENTS:
                print(f"🌊 Streaming from {provider}")

            async for token in STREAM_MAP[provider](prompt, system, max_tokens):
                yield token
            return  # Success — stop trying other providers

        except Exception as e:
            print(f"⚠️  {provider} stream failed: {e} — trying next")
            continue

    # All failed
    raise RuntimeError("All streaming providers failed")


# ─────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test that your LLM connections are working:
      python llm/providers.py
    """
    import asyncio

    async def test():
        print("\n🧪 Testing LLM providers...\n")

        # Test Groq (free — always test this first)
        print("1. Testing Groq (Tier 2)...")
        try:
            result = await call_llm(
                prompt="Say exactly: 'Groq is working'",
                tier="tier2",
                max_tokens=20,
                system="You are a test assistant. Follow instructions exactly.",
            )
            print(f"   ✅ Groq: {result.strip()}")
        except Exception as e:
            print(f"   ❌ Groq failed: {e}")

        # Test JSON parsing
        print("\n2. Testing JSON response...")
        try:
            data = await call_llm_json(
                prompt='Return this exact JSON: {"status": "ok", "value": 42}',
                tier="tier2",
                max_tokens=50,
            )
            print(f"   ✅ JSON parsing: {data}")
        except Exception as e:
            print(f"   ❌ JSON parsing failed: {e}")

        # Test Anthropic (only if key is set)
        if settings.ANTHROPIC_API_KEY:
            print("\n3. Testing Anthropic Claude (Tier 1)...")
            try:
                result = await call_llm(
                    prompt="Say exactly: 'Claude is working'",
                    tier="tier1",
                    max_tokens=20,
                    system="You are a test assistant. Follow instructions exactly.",
                )
                print(f"   ✅ Claude: {result.strip()}")
            except Exception as e:
                print(f"   ❌ Claude failed: {e}")
        else:
            print("\n3. Skipping Anthropic test — no API key set")

        # Show spend summary
        print(f"\n📊 Spend today: ${spend_tracker.summary()['usd_today']}")
        print(f"   Tokens used: {spend_tracker.summary()['tokens_today']}")
        print(f"   Calls made:  {spend_tracker.summary()['calls_today']}")
        print("\n✅ Provider tests complete\n")

    asyncio.run(test())