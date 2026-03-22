"""
agents/prediction_logger.py — Extracts and logs verifiable predictions
========================================================================
The Prediction Logger scans all agent outputs for falsifiable claims —
statements that can be verified as true or false in the future.

Examples of loggable predictions:
  "Canadian tech hiring will slow 10-15% within 6 months"
  "Oil prices will rise above $90/barrel within 3 months"
  "USD/CAD will reach 1.42 within 12 months"

These are stored in state.predictions and saved to SQLite for the
feedback loop — after 30/90 days, a verifier job checks which were right.

This is what gives Cascade credibility over time: a track record.

Tier: tier2 (Groq) — extraction task, doesn't need Claude reasoning
"""

import asyncio
import sqlite3
import os
from datetime import datetime, timezone, timedelta

from config import settings
from llm.providers import call_llm_json
from graph.state import CascadeState, PredictionEntry


PREDICTION_SYSTEM = """You extract falsifiable predictions from analyst reports.
A falsifiable prediction must: specify a measurable outcome, a direction, and a timeframe.
Respond with valid JSON only."""


async def run_prediction_logger(state: CascadeState) -> CascadeState:
    """
    Extracts predictions from agent outputs and saves them for future verification.
    This is a side-effect node — it always returns the state unchanged.
    """
    completed = state.get_completed_agents()
    if not completed:
        return state

    # Build a compact list of findings for extraction
    findings_text = "\n".join(
        f"[{state.agent_outputs[n].domain}] {state.agent_outputs[n].finding[:300]}"
        for n in completed[:8]
    )

    prompt = f"""Extract 3-6 verifiable predictions from these analyst findings:

FINDINGS:
{findings_text}

A valid prediction must be measurable and have a clear timeframe.
Return JSON:
{{
  "predictions": [
    {{
      "claim":          "specific measurable prediction",
      "domain":         "domain key",
      "direction":      "increase|decrease|stable",
      "timeframe_days": 30 or 90 or 180 or 365,
      "confidence":     0.0-1.0
    }}
  ]
}}"""

    try:
        data = await asyncio.wait_for(
            call_llm_json(
                prompt=prompt,
                tier="tier2",
                max_tokens=400,
                system=PREDICTION_SYSTEM,
            ),
            timeout=15,
        )

        raw_preds = data.get("predictions", [])
        entries   = []
        now       = datetime.now(timezone.utc)

        for p in raw_preds[:6]:
            days = int(p.get("timeframe_days", 90))
            verify_date = (now + timedelta(days=days)).date().isoformat()

            entry = PredictionEntry(
                claim=             str(p.get("claim", "")),
                domain=            str(p.get("domain", "")),
                direction=         str(p.get("direction", "")),
                timeframe_days=    days,
                confidence=        float(p.get("confidence", 0.5)),
                verification_date= verify_date,
            )
            entries.append(entry)

        state.predictions = entries

        # Persist to SQLite for the feedback loop
        _save_to_db(state.run_id, state.query, entries)

        if settings.DEBUG_AGENTS:
            print(f"📝 Prediction logger: {len(entries)} predictions saved")

    except Exception as e:
        print(f"⚠️  Prediction logger failed: {e}")
        # Non-critical — don't add to state errors

    return state


def _save_to_db(run_id: str, query: str, predictions: list[PredictionEntry]) -> None:
    """
    Persists predictions to SQLite for future verification.
    Creates the table if it doesn't exist yet.
    """
    if not predictions:
        return

    db_path = settings.PREDICTION_DB_PATH
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id                TEXT PRIMARY KEY,
                run_id            TEXT,
                query             TEXT,
                claim             TEXT,
                domain            TEXT,
                direction         TEXT,
                timeframe_days    INTEGER,
                confidence        REAL,
                generated_at      TEXT,
                verification_date TEXT,
                status            TEXT DEFAULT 'pending',
                actual_outcome    TEXT DEFAULT ''
            )
        """)

        for pred in predictions:
            cursor.execute("""
                INSERT OR IGNORE INTO predictions
                  (id, run_id, query, claim, domain, direction,
                   timeframe_days, confidence, generated_at, verification_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred.id, run_id, query[:200], pred.claim, pred.domain,
                pred.direction, pred.timeframe_days, pred.confidence,
                pred.generated_at, pred.verification_date, "pending",
            ))

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print(f"⚠️  Prediction DB write failed: {e}")
