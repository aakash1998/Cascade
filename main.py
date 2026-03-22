"""
main.py — Cascade application entry point
==========================================
This is where the FastAPI app lives. It does three things:

  1. Creates the FastAPI app and sets up CORS
     (CORS lets your frontend at localhost:3000 talk to the
      backend at localhost:8000 without browser blocking it)

  2. Defines the API routes:
     - GET  /          → serves the frontend HTML
     - GET  /health    → quick check that the app is alive
     - POST /profile   → saves the user's onboarding answers
     - GET  /stream    → the main SSE stream (this is where
                         agents run and stream results live)

  3. Starts the server when you run: python main.py

How to run:
  python main.py
  → open http://localhost:8000 in your browser

How SSE works:
  SSE (Server-Sent Events) is a simple HTTP protocol where
  the server keeps the connection open and pushes data to
  the browser as it becomes available — token by token.
  No WebSockets needed. Works in every browser natively.
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from graph.state import create_initial_state
from graph.pipeline import run_pipeline_streaming

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────

# Rate limiter — protects your API keys on the public demo
# Uses the visitor's IP address as the identifier
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Cascade — Ripple Effect Engine",
    description="Type any world event. Watch AI agents trace every ripple.",
    version="0.1.0",
    docs_url="/docs",       # Swagger UI at /docs — useful for testing
    redoc_url="/redoc",     # Alternative docs at /redoc
)

# Attach rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allows the frontend (any origin in dev) to call the API
# In production, replace "*" with your actual domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (CSS, JS) from the frontend folder
# This lets /static/style.css serve frontend/style.css
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except RuntimeError:
    # Frontend folder doesn't exist yet — that's fine for now
    pass


# ─────────────────────────────────────────────
# IN-MEMORY SESSION STORE
# ─────────────────────────────────────────────
# Stores active user sessions in RAM.
# Each session has: profile, conversation history, timestamps.
# Will be replaced with Azure SQL later.
# Sessions expire after SESSION_TTL_HOURS of inactivity.

sessions: dict = {}


def get_or_create_session(session_id: str) -> dict:
    """
    Returns an existing session or creates a new one.
    A session holds the user's profile and conversation history.
    """
    if session_id not in sessions:
        sessions[session_id] = {
            "session_id":   session_id,
            "profile":      {},           # user's onboarding answers
            "conversation": [],           # full message history
            "created_at":   datetime.utcnow().isoformat(),
            "last_active":  datetime.utcnow().isoformat(),
        }
    else:
        # Update last active time
        sessions[session_id]["last_active"] = datetime.utcnow().isoformat()
    return sessions[session_id]


def cleanup_expired_sessions() -> None:
    """
    Removes sessions that have been inactive longer than SESSION_TTL_HOURS.
    Called periodically to prevent memory leaks.
    """
    from datetime import timezone
    now = datetime.now(timezone.utc)
    ttl_hours = settings.SESSION_TTL_HOURS
    expired = []

    for sid, session in sessions.items():
        last = datetime.fromisoformat(session["last_active"])
        # Make last_active timezone-aware if it isn't
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        diff_hours = (now - last).total_seconds() / 3600
        if diff_hours > ttl_hours:
            expired.append(sid)

    for sid in expired:
        del sessions[sid]

    if expired:
        print(f"🧹 Cleaned up {len(expired)} expired session(s)")


# ─────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────

class UserProfile(BaseModel):
    """
    The user's onboarding answers.
    All fields are optional — user can skip any question.
    Stored in session memory and injected into the Personaliser agent.
    """
    job:              Optional[str] = None   # "Software engineer"
    city:             Optional[str] = None   # "Calgary, Canada"
    sector:           Optional[str] = None   # "Tech"
    household:        Optional[str] = None   # "Family with kids"
    housing:          Optional[str] = None   # "Own with mortgage"
    income_bracket:   Optional[str] = None   # "$60k-$100k"
    extra_context:    Optional[str] = None   # "I have savings in USD"


class QueryRequest(BaseModel):
    """
    A query submitted by the user.
    session_id links this query to the user's profile and history.
    """
    query:      str                   # "What does the US-China trade war mean for me?"
    session_id: Optional[str] = None  # UUID — generated by frontend on first visit


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Serves the main frontend HTML page.
    If the frontend file doesn't exist yet, returns a placeholder.
    """
    try:
        with open("frontend/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Placeholder until we build the frontend
        return HTMLResponse(content="""
        <html>
          <body style="font-family:sans-serif;padding:40px;max-width:600px;margin:auto">
            <h1>🌊 Cascade</h1>
            <p>Backend is running. Frontend coming soon.</p>
            <p>Test the API at <a href="/docs">/docs</a></p>
          </body>
        </html>
        """)


@app.get("/health")
async def health_check():
    """
    Quick health check endpoint.
    Returns app status, active session count, and key availability.
    Useful for monitoring and debugging.
    """
    from data.cache import cache
    return JSONResponse({
        "status":           "ok",
        "version":          "0.1.0",
        "active_sessions":  len(sessions),
        "groq_ready":       bool(settings.GROQ_API_KEY),
        "anthropic_ready":  bool(settings.ANTHROPIC_API_KEY),
        "tavily_ready":     bool(settings.TAVILY_API_KEY),
        "finnhub_ready":    bool(settings.FINNHUB_API_KEY),
        "free_mode":        settings.FREE_MODE_ONLY,
        "debug_mode":       settings.DEBUG_AGENTS,
        "cache":            cache.stats(),
        "timestamp":        datetime.utcnow().isoformat(),
    })


@app.post("/profile")
async def save_profile(profile: UserProfile, request: Request):
    """
    Saves the user's onboarding profile to their session.
    Called once after the user answers the 7 onboarding questions.

    The profile is stored in session memory and used by the
    Personaliser agent to make the analysis personal to this user.
    """
    # Get session_id from query params or generate a new one
    session_id = request.query_params.get("session_id") or str(uuid.uuid4())
    session = get_or_create_session(session_id)

    # Store profile — only non-null fields
    session["profile"] = {k: v for k, v in profile.dict().items() if v is not None}

    if settings.DEBUG_AGENTS:
        print(f"📝 Profile saved for session {session_id[:8]}...")
        print(f"   {session['profile']}")

    return JSONResponse({
        "status":     "ok",
        "session_id": session_id,
        "profile":    session["profile"],
    })


@app.get("/stream")
@limiter.limit(f"{settings.RATE_LIMIT_PER_IP_PER_DAY}/day")
async def cascade_stream(
    request:    Request,
    query:      str,
    session_id: Optional[str] = None,
):
    """
    THE MAIN ENDPOINT — this is where Cascade actually runs.

    Takes a user query and streams back the full analysis as
    Server-Sent Events (SSE). The browser receives events in
    real time as each agent finishes — one event per agent result.

    Event types the frontend receives:
      { type: "status",       message: "Analysing complexity..." }
      { type: "manifest",     data: { agents: [...], complexity: 4.2 } }
      { type: "data_fetched", sources: ["FRED", "GDELT", "Tavily"] }
      { type: "agent_result", agent: "Energy", finding: "...", confidence: 0.82 }
      { type: "chain_token",  token: "..." }   ← streams the ripple chain word by word
      { type: "personal",     token: "..." }   ← streams the personal impact
      { type: "summary",      token: "..." }   ← streams the final summary
      { type: "done",         share_id: "abc123" }
      { type: "error",        message: "..." }
    """
    # Get or create session
    sid = session_id or str(uuid.uuid4())
    session = get_or_create_session(sid)

    # Basic input validation
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if len(query) > 500:
        query = query[:500]  # Truncate silently — frontend should enforce this too

    # Clean up expired sessions periodically
    # (simple approach — runs on every 10th request)
    if len(sessions) % 10 == 0:
        cleanup_expired_sessions()

    # ── Add query to conversation history ─────────────────────
    session["conversation"].append({
        "role":      "user",
        "content":   query,
        "timestamp": datetime.utcnow().isoformat(),
    })

    # ── Build initial state ────────────────────────────────────
    initial_state = create_initial_state(
        query=      query,
        session_id= sid,
        profile=    session.get("profile", {}),
        history=    session.get("conversation", []),
    )

    async def event_stream():
        """
        Connects the pipeline to the SSE stream.

        Pattern:
          1. Create an asyncio.Queue to receive events from the pipeline.
          2. Run the pipeline in a background task — it puts events into the queue.
          3. This generator reads from the queue and yields SSE events.
          4. A heartbeat runs every 15s to keep the connection alive.
          5. When the pipeline puts a "done" event, we stop.
        """
        event_queue:   asyncio.Queue = asyncio.Queue()
        pipeline_task: asyncio.Task  = None

        try:
            # Yield first status immediately so the browser knows we're alive
            yield {
                "data": json.dumps({
                    "type":       "status",
                    "message":    "Query received — starting Cascade...",
                    "session_id": sid,
                })
            }
            await asyncio.sleep(0)

            # Start pipeline as a background task
            pipeline_task = asyncio.create_task(
                run_pipeline_streaming(initial_state, event_queue)
            )

            # Drain events from the queue and yield them to the browser
            done_seen = False
            while not done_seen:
                try:
                    # Wait up to 15s for the next event (heartbeat interval)
                    event = await asyncio.wait_for(event_queue.get(), timeout=15)
                    yield event

                    # Check if pipeline finished
                    payload = json.loads(event.get("data", "{}"))
                    if payload.get("type") in ("done", "error"):
                        done_seen = True

                    event_queue.task_done()

                except asyncio.TimeoutError:
                    # No event in 15s — send heartbeat to keep connection alive
                    yield {"data": json.dumps({"type": "heartbeat"})}

                except asyncio.CancelledError:
                    break

            # Wait for pipeline to finish cleanly
            if pipeline_task and not pipeline_task.done():
                try:
                    final_state = await asyncio.wait_for(pipeline_task, timeout=5)
                    # Save assistant turn to conversation history
                    if final_state and final_state.summary:
                        session["conversation"].append({
                            "role":      "assistant",
                            "content":   final_state.summary[:500],
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                except asyncio.TimeoutError:
                    pipeline_task.cancel()

        except asyncio.CancelledError:
            # Browser disconnected mid-stream
            if settings.DEBUG_AGENTS:
                print(f"🔌 Client disconnected: session {sid[:8]}")
            if pipeline_task and not pipeline_task.done():
                pipeline_task.cancel()

        except Exception as e:
            print(f"❌ Stream error for session {sid[:8]}: {e}")
            yield {
                "data": json.dumps({
                    "type":    "error",
                    "message": "An unexpected error occurred. Please try again.",
                })
            }
            if pipeline_task and not pipeline_task.done():
                pipeline_task.cancel()

    return EventSourceResponse(event_stream())


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Returns the current state of a session.
    Useful for debugging — see what profile and history a session has.
    Not exposed in the public UI.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    # Don't expose full conversation history in this endpoint
    return JSONResponse({
        "session_id":        session["session_id"],
        "profile":           session["profile"],
        "conversation_turns": len(session["conversation"]),
        "created_at":        session["created_at"],
        "last_active":       session["last_active"],
    })


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Deletes a session. Called when user explicitly clears their data.
    """
    if session_id in sessions:
        del sessions[session_id]
    return JSONResponse({"status": "ok", "message": "Session cleared"})


# ─────────────────────────────────────────────
# STARTUP + SHUTDOWN EVENTS
# ─────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    """
    Runs once when the app starts.
    Good place for: DB connection checks, warming up caches, etc.
    """
    print("\n" + "="*50)
    print("🌊  Cascade is starting up...")
    print("="*50)
    print(f"  Groq ready:       {'✅' if settings.GROQ_API_KEY else '❌'}")
    print(f"  Anthropic ready:  {'✅' if settings.ANTHROPIC_API_KEY else '⚠️  free mode'}")
    print(f"  Tavily ready:     {'✅' if settings.TAVILY_API_KEY else '❌'}")
    print(f"  Finnhub ready:    {'✅' if settings.FINNHUB_API_KEY else '❌'}")
    print(f"  Max agents:       {settings.MAX_AGENTS}")
    print(f"  Daily budget:     ${settings.DAILY_BUDGET_USD}")
    print(f"  Debug mode:       {settings.DEBUG_AGENTS}")
    print("="*50)
    print("  Docs:  http://localhost:8000/docs")
    print("  App:   http://localhost:8000")
    print("="*50 + "\n")


@app.on_event("shutdown")
async def on_shutdown():
    """
    Runs once when the app shuts down (Ctrl+C).
    Good place for: closing DB connections, flushing logs, etc.
    """
    print("\n👋 Cascade shutting down — goodbye\n")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run the app directly with: python main.py
    
    reload=True means the server auto-restarts when you save a file.
    Very useful during development — no need to manually restart.
    Turn off in production.
    """
    import os
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,       # auto-restart on file changes
        log_level="info",
    )