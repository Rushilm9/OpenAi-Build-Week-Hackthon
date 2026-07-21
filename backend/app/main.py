from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth
from app.api.routes import analysis
from app.api.routes import alerts
from app.api.routes import smc
from app.api.routes import market
from app.api.routes import agentlogs
from app.core.scheduler import start_scheduler, stop_scheduler
from app.core.config import logger, get_llm_info, settings
from app.services.mcp_client import log_mcp_config, is_healthy as mcp_is_healthy, ping as mcp_ping
import logging
import time


# ── Suppress noisy access-log entries ──────────────────────────────────────
# The test console polls /health every 15 s and static assets are fetched
# on every page load. Neither is useful in the terminal. This filter drops
# those lines from uvicorn's access logger without affecting anything else.
_SILENT_PATHS = {"/health", "/mcp/health", "/docs", "/openapi.json", "/favicon.ico"}

class _SilentPathFilter(logging.Filter):
    """Drop uvicorn access-log records for health/static/docs paths."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        # uvicorn access records look like:
        #   127.0.0.1:12345 - "GET /health HTTP/1.1" 200 OK
        for path in _SILENT_PATHS:
            if f'"GET {path} ' in msg or f'"HEAD {path} ' in msg:
                return False
        # Also suppress requests for static assets (js, css, fonts, icons)
        for ext in (".js", ".css", ".woff", ".woff2", ".png", ".ico", ".svg", ".map"):
            if f'"{ext}' in msg or ext + " HTTP" in msg:
                return False
        return True

_access_filter = _SilentPathFilter()





@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[bold green]🚀 Starting Quant AI Backend...[/bold green]")
    get_llm_info()

    # Auto-create tables for SQLite (idempotent — no-ops if tables exist)
    try:
        from app.core.config import engine
        from app.db.models import Base
        if engine:
            Base.metadata.create_all(bind=engine)
            logger.info("[bold green]✓ Database tables verified/created.[/bold green]")
    except Exception as _e:
        logger.warning(f"[yellow]Table creation skipped: {_e}[/yellow]")

    start_scheduler()

    # ── Startup Tasks (Deferred to run asynchronously after startup) ──
    async def run_startup_tasks():
        import asyncio
        # Wait a tiny bit for the web server to bind to the port
        await asyncio.sleep(0.1)
        
        try:
            log_mcp_config()
        except Exception as _e:
            logger.warning(f"[yellow]Deferred log_mcp_config failed: {_e}[/yellow]")

        # 2. Best-effort initial probe so /mcp/health is meaningful right away.
        try:
            # Run in thread pool to avoid blocking the event loop
            ok = await asyncio.to_thread(mcp_ping, True)
            logger.info(f"[bold {'green' if ok else 'yellow'}]MCP initial probe: {'UP' if ok else 'DOWN'}[/bold {'green' if ok else 'yellow'}]")
        except Exception as _e:
            logger.warning(f"[yellow]MCP initial probe error: {_e}[/yellow]")

    import asyncio
    asyncio.create_task(run_startup_tasks())

    # Attach the access-log filter so health polls don't clog the terminal
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addFilter(_access_filter)
    logger.info("[bold green]✓ Quant AI Backend is ready![/bold green]")
    yield

    # Shutdown
    uvicorn_access.removeFilter(_access_filter)
    logger.info("[bold red]Stopping Quant AI Backend...[/bold red]")
    stop_scheduler()


# Initialize FastAPI app
app = FastAPI(
    title="Quant AI",
    description="Multi-agent Indian stock intelligence system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware — only log meaningful API calls
# Adds (TEST_REPORT.md issue #4) a completion line with elapsed time + a clear
# CLIENT-DISCONNECT marker for long handlers so operators can correlate slow
# /discover runs even when the client socket dropped.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    skip = (
        path in _SILENT_PATHS
        or path.startswith("/static")
        or any(path.endswith(ext) for ext in (".js", ".css", ".woff", ".woff2", ".png", ".ico", ".svg", ".map"))
    )
    if not skip:
        logger.info(f" [dim]← {request.method} {path}[/dim]")

    t0 = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed = round(time.time() - t0, 2)
        # Starlette raises ClientDisconnect on dropped sockets; log it cleanly
        name = type(exc).__name__
        if name == "ClientDisconnect":
            if not skip:
                logger.warning(
                    f" [yellow]→ CLIENT-DISCONNECT {request.method} {path} after {elapsed}s "
                    f"(handler may still be running)[/yellow]"
                )
        else:
            logger.error(f" [red]→ ERROR {request.method} {path} after {elapsed}s: {name}: {exc}[/red]")
        raise

    elapsed = round(time.time() - t0, 2)
    if not skip and elapsed >= 1.0:
        # Only log slow successes; fast handlers are uvicorn-access-log territory.
        logger.info(f" [dim]→ {response.status_code} {request.method} {path} ({elapsed}s)[/dim]")
    return response


# Register routes
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(alerts.router)
app.include_router(smc.router)
app.include_router(market.router)
app.include_router(agentlogs.router)


# ── /failures endpoint ────────────────────────────────────────────────────
from app.services.failure_log import get_recent_failures, clear_all_logs

@app.get("/failures", tags=["QA"], summary="Recent pipeline failure log entries")
def get_failures(limit: int = 50):
    """Returns the most recent structured failure log entries from qa_logs/failed_log.jsonl."""
    return {"failures": get_recent_failures(limit=limit), "count": min(limit, 9999)}


@app.delete("/logs", tags=["QA"], summary="Clear all pipeline logs")
def delete_logs(clear_db: bool = True):
    """
    Clears all failure log files (JSONL) and optionally the AgentLogs DB table.

    Query params:
        clear_db: If true (default), also truncates the AgentLogs table in the database.
    """
    result = clear_all_logs()

    # Optionally clear AgentLogs from DB
    db_cleared = 0
    if clear_db:
        try:
            from app.core.config import SessionLocal
            from app.db.models import AgentLogs
            if SessionLocal:
                db = SessionLocal()
                try:
                    db_cleared = db.query(AgentLogs).delete()
                    db.commit()
                except Exception as e:
                    db.rollback()
                    result["db_error"] = str(e)
                finally:
                    db.close()
        except Exception as e:
            result["db_error"] = str(e)

    result["db_agent_logs_cleared"] = db_cleared
    logger.info(f"[bold yellow]🧹 Logs cleared: {result['entries_removed']} file entries, {db_cleared} DB rows[/bold yellow]")
    return result

from fastapi.staticfiles import StaticFiles

@app.get("/health")
def health():
    from app.core.model_router import get_model_metadata

    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm": {**get_model_metadata(), "configured": bool(settings.OPENAI_API_KEY)},
    }


import os

@app.get("/api_keys/health", tags=["QA"], summary="Test configured LLM API keys")
async def api_keys_health():
    """Return secret-free OpenAI configuration metadata without a network call."""
    from app.core.model_router import get_model_metadata

    configured = bool(settings.OPENAI_API_KEY)
    return {
        "provider": "openai",
        "status": "configured" if configured else "missing",
        "key_configured": configured,
        **get_model_metadata(),
    }


@app.get("/connections/openai_check", tags=["QA"], summary="Test OpenAI Responses API")
async def openai_check():
    """Run an explicit OpenAI probe without returning credential data."""
    from app.core.model_router import get_model, get_model_id, get_model_metadata, ModelTier

    metadata = get_model_metadata()
    if not settings.OPENAI_API_KEY:
        return {
            "ok": False,
            "status": "missing",
            "detail": "OPENAI_API_KEY is not configured; no network request was made.",
            **metadata,
        }

    try:
        from langchain_core.messages import HumanMessage
        from app.core.llm import extract_content

        llm = get_model(ModelTier.DISCOVERY)
        response = await llm.ainvoke([HumanMessage(content="Reply with exactly OPENAI_OK.")])
        content = extract_content(response)
        probe_ok = content.strip().upper() == "OPENAI_OK"
        return {
            "ok": probe_ok,
            "status": "ok" if probe_ok else "error",
            "detail": (
                "OpenAI Responses API call succeeded."
                if probe_ok
                else "OpenAI responded, but the probe response was unexpected."
            ),
            "model": get_model_id(ModelTier.DISCOVERY),
            **metadata,
        }
    except Exception as e:
        logger.warning(f"OpenAI connection probe failed: {type(e).__name__}")
        return {
            "ok": False,
            "status": "error",
            "detail": "OpenAI Responses API call failed.",
            "error_type": type(e).__name__,
            **metadata,
        }


@app.get("/connections/health", tags=["QA"], summary="Test all API keys + the DB connection")
async def connections_health():
    """
    One-shot connectivity check for every external credential the app uses.

    Probes:
      - OpenAI       → secret-free configuration metadata
      - Database     → SELECT 1 via the configured SQLAlchemy engine
      - FRED / Finnhub / Alpha Vantage → configured?
    """
    from app.core.config import settings

    checks: dict[str, dict] = {}

    # ── OpenAI Responses API configuration (no network call) ────────────────
    from app.core.model_router import get_model_metadata

    openai_configured = bool(settings.OPENAI_API_KEY)
    checks["openai"] = {
        "name": "OPENAI_API_KEY",
        "status": "configured" if openai_configured else "missing",
        "detail": (
            "OpenAI Responses API is configured."
            if openai_configured
            else "OPENAI_API_KEY is not configured; no network request was made."
        ),
        **get_model_metadata(),
    }

    # ── Database (live SELECT 1) ────────────────────────────────────────────
    db_check = {"status": "error", "detail": "unknown"}
    try:
        from app.core.config import SessionLocal
        from sqlalchemy import text as _text
        if not SessionLocal:
            db_check = {"status": "error", "detail": "SessionLocal not initialized (DB connect failed at startup)"}
        else:
            db = SessionLocal()
            try:
                db.execute(_text("SELECT 1"))
                db_check = {"status": "ok", "detail": "SELECT 1 succeeded."}
            finally:
                db.close()
    except Exception as e:
        db_check = {"status": "error", "detail": f"{type(e).__name__}: {e}"}
    checks["database"] = db_check

    # ── Data-provider keys ──────────────────────────────────────────────────
    providers = []
    for env_name in ("FRED_API_KEY", "FINNHUB_API_KEY", "ALPHA_VANTAGE_API_KEY"):
        val = os.getenv(env_name, "")
        providers.append({
            "name": env_name,
            "status": "configured" if val else "missing",
            "detail": "env var set" if val else "not set (provider falls back / skips)",
        })
    checks["data_providers"] = providers

    # ── Market-data MCP server ───────────────────────────────────────────────
    mcp_snapshot = mcp_is_healthy()
    checks["market_data_mcp"] = {
        "status": "ok" if mcp_snapshot.get("ok") else "unavailable",
        "detail": mcp_snapshot.get("detail") or "No successful market-data MCP probe yet.",
    }

    # ── Arize MCP Server ────────────────────────────────────────────────────
    if settings.ARIZE_MCP_ENABLED and settings.PHOENIX_API_KEY:
        checks["arize_mcp"] = {"status": "configured", "detail": "Arize Phoenix MCP is configured."}
    else:
        checks["arize_mcp"] = {"status": "missing", "detail": "Arize Phoenix MCP is not configured."}

    # ── Top-level readiness ──────────────────────────────────────────────────
    openai_ok = openai_configured

    # ── Top-level ok ────────────────────────────────────────────────────────
    live_ok = openai_ok and db_check["status"] == "ok"

    return {"ok": live_ok, "checks": checks}


@app.get("/mcp/health", tags=["MCP"])
def mcp_health():
    """Probe the upstream MCP server. Cached for MCP_HEALTH_TTL seconds."""
    result = mcp_is_healthy()
    # Add a 'status' field so test_endpoints.py can check it
    result["status"] = "healthy" if result.get("ok") else "unhealthy"
    return result

@app.get("/debug/summary", tags=["QA"], summary="Consolidated debug snapshot")
def debug_summary(failures_limit: int = 100, agent_logs_limit: int = 50):
    """
    Returns a consolidated debug snapshot:
    - Recent structured pipeline failures (from JSONL)
    - MCP server health
    - Recent AgentLogs from DB (agent name, status, error, latency, run_id)
    - Recent Runs from DB (id, status, workflow_name, started_at, completed_at)
    - Discovery job queue state
    - Analysis dispatcher state (per run_id summary)
    """
    import datetime

    # 1. Pipeline failures from JSONL
    from app.services.failure_log import get_recent_failures
    failures = get_recent_failures(limit=failures_limit)

    # 2. MCP health
    from app.services.mcp_client import is_healthy as mcp_is_healthy
    mcp_health = mcp_is_healthy()

    # 3. AgentLogs from DB (most recent N rows, FAILED ones first then rest)
    agent_logs = []
    try:
        from app.core.config import SessionLocal
        from app.db.models import AgentLogs
        if SessionLocal:
            db = SessionLocal()
            try:
                rows = (
                    db.query(AgentLogs)
                    .order_by(AgentLogs.created_at.desc())
                    .limit(agent_logs_limit)
                    .all()
                )
                for r in rows:
                    agent_logs.append({
                        "id": str(r.id),
                        "run_id": str(r.run_id) if r.run_id else None,
                        "agent_name": r.agent_name,
                        "agent_type": r.agent_type,
                        "status": r.status,
                        "error": r.error,
                        "latency_ms": float(r.latency_ms) if r.latency_ms is not None else None,
                        "model_used": r.model_used,
                        "signal": r.signal,
                        "confidence": float(r.confidence) if r.confidence is not None else None,
                        "tokens_input": r.tokens_input,
                        "tokens_output": r.tokens_output,
                        "cost_usd": float(r.cost_usd) if r.cost_usd is not None else None,
                        "retry_count": r.retry_count,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    })
            finally:
                db.close()
    except Exception as e:
        agent_logs = [{"error": f"DB read failed: {e}"}]

    # 4. Recent Runs from DB
    recent_runs = []
    try:
        from app.core.config import SessionLocal
        from app.db.models import Runs
        if SessionLocal:
            db = SessionLocal()
            try:
                rows = (
                    db.query(Runs)
                    .order_by(Runs.started_at.desc())
                    .limit(20)
                    .all()
                )
                for r in rows:
                    recent_runs.append({
                        "id": str(r.id),
                        "workflow_name": r.workflow_name,
                        "status": r.status,
                        "started_at": r.started_at.isoformat() if r.started_at else None,
                        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                        "elapsed_sec": round(
                            (r.completed_at - r.started_at).total_seconds(), 1
                        ) if r.completed_at and r.started_at else None,
                    })
            finally:
                db.close()
    except Exception as e:
        recent_runs = [{"error": f"DB read failed: {e}"}]

    # 5. Discovery job queue state
    discovery_jobs = []
    try:
        from app.services.discovery_cache import list_jobs
        discovery_jobs = list_jobs(limit=10)
    except Exception as e:
        discovery_jobs = [{"error": str(e)}]

    # 6. Analysis dispatcher state
    dispatch_state = {}
    try:
        from app.services.analysis_dispatcher import get_status, _status_store, _status_lock
        import threading
        with _status_lock:
            run_ids = list(_status_store.keys())
        for rid in run_ids[-5:]:  # last 5 run_ids
            dispatch_state[rid] = get_status(rid)
    except Exception as e:
        dispatch_state = {"error": str(e)}

    # Discovery job results embed raw screener stock data (RSI/close/…) that can
    # contain NaN/inf floats. FastAPI's JSON encoder rejects those with HTTP 500
    # ("Out of range float values are not JSON compliant"). Scrub them to null so
    # the Debug Console stays alive once a discovery job has run.
    return _json_safe({
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "failures": failures,
        "failures_count": len(failures),
        "mcp": mcp_health,
        "agent_logs": agent_logs,
        "recent_runs": recent_runs,
        "discovery_jobs": discovery_jobs,
        "dispatch_state": dispatch_state,
    })


def _json_safe(obj):
    """Recursively replace NaN/inf floats with None so the result is JSON-compliant.
    FastAPI's default encoder raises on non-finite floats (which leak in via raw
    screener data inside discovery job results)."""
    import math
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


# ── /logs HTML page ──────────────────────────────────────────────────────
# Standalone debug UI at /logs. Reads the existing /debug/summary JSON every
# 30s and renders failures + agent logs + runs + jobs in a single page.
# Route is registered BEFORE the static mount below so it wins over the
# StaticFiles catch-all.
from fastapi.responses import FileResponse
from pathlib import Path as _Path

_LOGS_HTML = _Path(__file__).parent.parent / "frontend" / "logs.html"
_AGENTLOGS_HTML = _Path(__file__).parent.parent / "frontend" / "agentlogs.html"
_EVALS_HTML = _Path(__file__).parent.parent / "frontend" / "evals.html"

@app.get("/logs", include_in_schema=False)
def logs_page():
    """Standalone debug UI: pipeline failures, agent logs, recent runs, MCP status."""
    return FileResponse(str(_LOGS_HTML), media_type="text/html")

@app.get("/agentlogs", include_in_schema=False)
def agentlogs_page():
    """Detailed per-agent drill-down UI: run list → agent timeline → per-agent payloads."""
    return FileResponse(str(_AGENTLOGS_HTML), media_type="text/html")

@app.get("/evals", include_in_schema=False)
def evals_page():
    """LLM-as-Judge dashboard: per-stock evaluator scores read from Phoenix via MCP."""
    return FileResponse(str(_EVALS_HTML), media_type="text/html")

# Server-side cache of the last successful MCP experiment read. Each MCP call
# cold-spawns an `npx @arizeai/phoenix-mcp` subprocess (~6s), so without this every
# page load shows a multi-second spinner. We cache the result and serve it instantly;
# the UI's "Refresh" button passes force=true to bypass and re-read over MCP.
_EVALS_CACHE: dict = {"data": None, "ts": 0.0}
_EVALS_CACHE_TTL_SEC = 600  # 10 min; Refresh forces a fresh read regardless

@app.get("/api/evals/experiment", tags=["Evals"], summary="Latest experiment evaluator results (read via Phoenix MCP)")
async def get_experiment_evals(dataset_name: str = "wait-discipline-stocks", force: bool = False):
    """Read the latest experiment's LLM-as-judge + deterministic eval results from
    Phoenix Cloud over MCP. The judges execute in eval/run_experiment.py (phoenix.evals);
    this endpoint is the MCP read-back layer that feeds the /evals frontend.

    Cached server-side (see _EVALS_CACHE) so page loads are instant; pass force=true
    (the UI Refresh button) to bypass the cache and re-read over MCP."""
    import time as _time
    from app.core.config import settings
    if not settings.ARIZE_MCP_ENABLED:
        return JSONResponse(
            {"rows": [], "evaluators": [], "error": "ARIZE_MCP_ENABLED is not true — MCP read-back disabled."},
            status_code=200,
        )

    # Serve from cache unless forced or stale.
    if not force and _EVALS_CACHE["data"] is not None and (_time.time() - _EVALS_CACHE["ts"]) < _EVALS_CACHE_TTL_SEC:
        cached = dict(_EVALS_CACHE["data"])
        cached["cached"] = True
        return JSONResponse(cached, status_code=200)

    try:
        from app.core.phoenix_mcp import PhoenixMCP
        async with PhoenixMCP() as mcp:
            data = await mcp.get_latest_experiment_evals(dataset_name=dataset_name)
        # Build a compare-URL so the UI can deep-link into Phoenix Cloud.
        endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "https://app.phoenix.arize.com")
        base_url = endpoint.split("/v1/traces")[0] if "/v1/traces" in endpoint else endpoint
        data["phoenix_base_url"] = base_url
        data["cached"] = False
        # Only cache successful reads (don't pin an error/empty result).
        if data.get("rows"):
            _EVALS_CACHE["data"] = data
            _EVALS_CACHE["ts"] = _time.time()
        return JSONResponse(data, status_code=200)
    except Exception as e:
        # On failure, fall back to stale cache if we have one.
        if _EVALS_CACHE["data"] is not None:
            stale = dict(_EVALS_CACHE["data"])
            stale["cached"] = True
            stale["stale"] = True
            return JSONResponse(stale, status_code=200)
        return JSONResponse({"rows": [], "evaluators": [], "error": str(e)}, status_code=200)

@app.get("/config.js", include_in_schema=False)
def config_js():
    """Single source of truth for the frontend's API base URL.

    Emits `window.__API_BASE__` from the PUBLIC_API_BASE_URL setting. Blank
    means the frontend falls back to its own origin. This is the one place to
    configure the backend base URL for every HTML page.
    """
    import json as _json
    from fastapi.responses import Response
    from app.core.config import settings
    base = settings.PUBLIC_API_BASE_URL or ""
    body = f"window.__API_BASE__ = {_json.dumps(base)};\n"
    return Response(content=body, media_type="application/javascript")

from pydantic import BaseModel, field_validator
from fastapi.responses import JSONResponse

# NOTE: Phoenix Cloud normalizes prompt names by stripping non-alphanumeric
# characters — `create_prompt("decision-narrative-prompt")` is stored as
# `decisionnarrativeprompt`, but `list-prompt-versions`/`get_prompt` queried with
# the hyphenated name return 0 versions → the improve loop could never find its
# own candidate. We use the already-normalized canonical name so write == read,
# and normalize whatever name clients send (the React frontend still sends the
# hyphenated form) so every caller reads/writes the same Phoenix prompt.
_PROMPT_NAME = "decisionnarrativeprompt"

def _normalize_prompt_name(v: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9]", "", v or "") or _PROMPT_NAME

class ImproveRequest(BaseModel):
    prompt_name: str = _PROMPT_NAME

    _norm = field_validator("prompt_name")(staticmethod(_normalize_prompt_name))

class ApproveRequest(BaseModel):
    prompt_name: str = _PROMPT_NAME
    candidate_tag: str = "candidate"
    production_tag: str = "production"

    _norm = field_validator("prompt_name")(staticmethod(_normalize_prompt_name))

# ── Phase 7B: Self-improving loop API endpoints ──────────────────────────

@app.post("/api/improve/propose", tags=["Improve"], summary="Run Improver and upsert candidate prompt")
async def improve_propose(req: ImproveRequest):
    from app.core.config import settings
    if not settings.ARIZE_MCP_ENABLED:
        return JSONResponse({"error": "ARIZE_MCP_ENABLED is not true"}, status_code=400)

    from app.core.phoenix_mcp import PhoenixMCP

    # Detect failed decisions from the DB rather than Phoenix span annotations.
    # Live per-decision span annotations don't land reliably (LangGraph runs the
    # decision node in a thread pool where the OTel span context isn't current),
    # so reading them gave 0 failures. The DB has the same deterministic signal:
    # a FAIL = a non-WAIT decision that the validator rejected OR confidence < 60.
    def _fetch_failures() -> list[dict]:
        from app.core.config import SessionLocal
        from app.db.models import Recommendations, Stocks
        if not SessionLocal:
            return []
        db = SessionLocal()
        try:
            rows = (
                db.query(Recommendations, Stocks.symbol)
                .join(Stocks, Recommendations.stock_id == Stocks.id)
                .order_by(Recommendations.created_at.desc())
                .limit(200)
                .all()
            )
        finally:
            db.close()
        fails = []
        for rec, sym in rows:
            action = (rec.recommendation or "").upper()
            accepted = (rec.validator_status or "").lower() == "accepted"
            # The validator overwrites rejected decisions to WAIT, so a WAIT row
            # is only a genuine low-conviction refusal when the validator accepted
            # it. Rejected-and-forced-to-WAIT rows ARE the failures.
            if action == "WAIT" and accepted:
                continue
            try:
                c = float(rec.confidence) if rec.confidence is not None else 0.0
            except (TypeError, ValueError):
                c = 0.0
            if c <= 1.0:
                c *= 100
            if not accepted or c < 60:
                # Recover the action the validator rejected and why; the stored
                # recommendation is the post-rejection WAIT, not what the agent chose.
                original, note = action, ""
                issues = rec.validator_issues or []
                if isinstance(issues, list):
                    for issue in issues:
                        if isinstance(issue, dict) and issue.get("action") == "force_wait":
                            if issue.get("rec_before"):
                                original = str(issue["rec_before"]).upper()
                            elif issue.get("field") == "recommendation" and issue.get("before"):
                                original = str(issue["before"]).upper()
                            note = issue.get("note") or note
                reason = (
                    f"validator={'accepted' if accepted else 'rejected'}, confidence={round(c,1)}%"
                )
                if note:
                    reason += f" — {note}"
                fails.append({
                    "symbol": sym,
                    "recommendation": original,
                    "confidence": round(c, 1),
                    "validator_status": rec.validator_status,
                    "reason": reason,
                    "narrative": (rec.final_narrative or "")[:200] if hasattr(rec, "final_narrative") else "",
                })
        return fails

    try:
        import asyncio
        failed_decisions = await asyncio.to_thread(_fetch_failures)

        async with PhoenixMCP() as mcp:

            # Try to fetch the @production prompt; if it doesn't exist, auto-seed it.
            try:
                prompt_data = await mcp.get_prompt(name=req.prompt_name, version="production")
                current_template = prompt_data.get("template", "") if isinstance(prompt_data, dict) else ""
            except Exception:
                prompt_data = {}
                current_template = ""
            
            if not current_template:
                # Auto-seed the initial production prompt from the local decision node
                from app.agents.decision.prompts import DECISION_NARRATIVE_PROMPT
                seed_template = DECISION_NARRATIVE_PROMPT if DECISION_NARRATIVE_PROMPT else "You are a financial decision agent. Analyze all signals and make a BUY/SELL/WAIT recommendation."
                logger.info("[bold cyan]Seeding initial production prompt into Phoenix Cloud...[/bold cyan]")
                await mcp.create_prompt(
                    name=req.prompt_name,
                    template=seed_template,
                    description="Auto-seeded initial production prompt from local decision node",
                    version_tag="production"
                )
                current_template = seed_template

            if not failed_decisions:
                return {"status": "no_failures", "message": "No failed decisions found in the DB to improve."}

            failure_examples = []
            for idx, f in enumerate(failed_decisions[:5]):
                failure_examples.append(
                    f"Failure #{idx+1}: {f['symbol']} -> {f['recommendation']} "
                    f"({f['reason']}). Narrative: {f.get('narrative','')}"
                )

            failures_context = "\n".join(failure_examples)

            prompt_text = f"""Analyze the following failures and re-write the prompt template.

CURRENT SYSTEM PROMPT:
```
{current_template}
```

DETECTED FAILURE TRACES:
```
{failures_context}
```

YOUR TASK:
1. Analyze the failures and formulate a specific, clear instruction rule that directly prevents this mistake.
2. Re-write the SYSTEM PROMPT, embedding this new rule seamlessly.
3. Return your final analysis and the complete new prompt template in this JSON format:
{{
  "analysis": "YOUR_DETAILED_ANALYSIS_AND_PATTERN_IDENTIFIED",
  "new_rule": "THE_EXPLICIT_RULE_YOU_FORMULATED",
  "new_prompt_template": "THE_COMPLETE_V2_PROMPT_TEMPLATE_CONTAINING_THE_NEW_RULE"
}}"""

            from langchain_core.messages import HumanMessage
            from app.core.model_router import get_model, ModelTier
            from app.core.llm import extract_content
            import json
            import re

            llm = get_model(ModelTier.ANALYSIS)
            response_text = extract_content(llm.invoke([HumanMessage(content=prompt_text)]))

            # Robust parse: the improver returns a large JSON whose
            # new_prompt_template field is a full multi-line prompt with embedded
            # quotes/newlines, which trips a naive json.loads. Strip fences, then
            # slice first { .. last } and retry after removing trailing commas —
            # same hardening used by the discovery Stage-8 parser.
            def _parse_improver(raw: str) -> dict | None:
                txt = (raw or "").strip()
                if txt.startswith("```"):
                    txt = "\n".join(l for l in txt.split("\n") if not l.strip().startswith("```")).strip()
                cands = [txt]
                f, l = txt.find("{"), txt.rfind("}")
                if f != -1 and l != -1 and l > f:
                    cands.append(txt[f:l + 1])
                for c in cands:
                    try:
                        return json.loads(c)
                    except Exception:
                        try:
                            return json.loads(re.sub(r",(\s*[}\]])", r"\1", c))
                        except Exception:
                            continue
                return None

            improver_output = _parse_improver(response_text)
            if improver_output and improver_output.get("new_prompt_template"):
                new_prompt = improver_output["new_prompt_template"]
                analysis = improver_output.get("analysis", "")
                rule = improver_output.get("new_rule", "")
            else:
                analysis = "Improver JSON parse failed — appended a conservative policy note."
                rule = "Require explicit risk:reward justification before any BUY/SELL."
                new_prompt = current_template + "\n\nCRITICAL POLICY:\n- " + rule

            await mcp.create_prompt(
                name=req.prompt_name,
                template=new_prompt,
                description=f"Auto-patched: {rule[:50]}",
                version_tag="candidate"
            )

            return {
                "status": "success",
                "failures_analyzed": len(failed_decisions),
                "analysis": analysis,
                "rule": rule,
                "proposed_prompt": new_prompt
            }
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/improve/approve", tags=["Improve"], summary="Move production tag to candidate")
async def improve_approve(req: ApproveRequest):
    from app.core.config import settings
    if not settings.ARIZE_MCP_ENABLED:
        return JSONResponse({"error": "ARIZE_MCP_ENABLED is not true"}, status_code=400)

    from app.core.phoenix_mcp import PhoenixMCP
    try:
        async with PhoenixMCP() as mcp:
            versions_res = await mcp.call_tool("list-prompt-versions", {"prompt_identifier": req.prompt_name})
            import json
            if isinstance(versions_res, str):
                versions_res = json.loads(versions_res)
            
            versions = versions_res.get("data", []) if isinstance(versions_res, dict) else (versions_res if isinstance(versions_res, list) else [])
            
            candidate_id = None
            for v in versions:
                tags = v.get("tags", [])
                if req.candidate_tag in tags or req.candidate_tag in [t.get("name") if isinstance(t, dict) else t for t in tags]:
                    candidate_id = v.get("id")
                    break
            
            if not candidate_id and versions:
                candidate_id = versions[0].get("id")
                
            if candidate_id:
                await mcp.call_tool("add-prompt-version-tag", {
                    "prompt_version_id": candidate_id,
                    "name": req.production_tag
                })
                
                import asyncio
                import subprocess
                import os
                import sys

                def rerun_tests():
                    env = os.environ.copy()
                    env["PYTHONIOENCODING"] = "utf-8"
                    try:
                        # Use THIS interpreter (sys.executable), not bare "python".
                        # Bare "python" resolves to whatever is on PATH (often the
                        # base Anaconda env, which lacks phoenix) → the eval re-run
                        # dies with ModuleNotFoundError. sys.executable is the venv
                        # python the server is running under.
                        subprocess.run([sys.executable, "eval/run_experiment.py"], env=env, check=False)
                    except Exception as e:
                        from app.core.config import logger
                        logger.error(f"Failed to execute run_experiment.py: {e}")
                            
                asyncio.create_task(asyncio.to_thread(rerun_tests))
                
                return {"status": "success", "message": f"Approved {candidate_id} and rerunning test cases."}
            else:
                return JSONResponse({"status": "error", "message": "Candidate version not found."}, status_code=404)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/improve/reject", tags=["Improve"], summary="Discard candidate prompt")
async def improve_reject(req: ApproveRequest):
    from app.core.config import settings
    if not settings.ARIZE_MCP_ENABLED:
        return JSONResponse({"error": "ARIZE_MCP_ENABLED is not true"}, status_code=400)
    
    return {"status": "success", "message": "Candidate rejected. No tag movement."}

@app.get("/api/metrics", tags=["Improve"], summary="Aggregated decision-quality metrics from the DB")
async def improve_metrics():
    """Decision-quality pass-rate computed directly from the Recommendations DB.

    `decision_quality` is deterministic — it is the SAME rule annotate_decision
    writes to Phoenix spans: PASS = (validator accepted AND confidence >= 60) OR
    recommendation == WAIT (correctly refusing a low-conviction trade is good).
    We compute it from the DB rather than reading Phoenix span annotations, which
    avoids the span-indexing race and the OTel thread-context propagation issue
    that left live annotations unwritten. Source is the same data either way.
    """
    from app.core.config import settings, SessionLocal
    from app.db.models import Recommendations

    if not SessionLocal:
        return JSONResponse({"status": "error", "message": "DB not available"}, status_code=503)

    import asyncio

    def _compute() -> dict:
        db = SessionLocal()
        try:
            rows = db.query(
                Recommendations.recommendation,
                Recommendations.confidence,
                Recommendations.validator_status,
            ).all()
        finally:
            db.close()

        total = 0
        passed = 0
        for rec, conf, vstatus in rows:
            total += 1
            action = (rec or "").upper()
            try:
                c = float(conf) if conf is not None else 0.0
            except (TypeError, ValueError):
                c = 0.0
            if c <= 1.0:           # normalise legacy 0-1 scale to 0-100
                c *= 100
            accepted = (vstatus or "").lower() == "accepted"
            if action == "WAIT":
                passed += 1        # correctly refusing a low-conviction trade = good
            elif accepted and c >= 60:
                passed += 1

        pass_rate = round((passed / total) * 100, 2) if total > 0 else 0
        return {
            "status": "success",
            "source": "db",
            "metrics": {
                "total_evaluations": total,
                "passed": passed,
                "pass_rate_pct": pass_rate,
            },
        }

    try:
        return await asyncio.to_thread(_compute)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/arize/eval-summary", tags=["Improve"], summary="Arize dashboard summary (DB-derived)")
async def arize_eval_summary(hours: int = 72):
    """Aggregated observability summary for the Arize dashboard page.

    Computed from the DB (AgentLogs / Recommendations / Runs) over the last
    `hours` window. IMPORTANT — honest field sourcing:
      - Real, measured fields: evaluations, runs, retries, per-agent invocation/
        failure/success/confidence/tokens, token economics, recent spans, and
        safety_triggers (validator force-WAITs — a real safety layer firing).
      - hallucination_rate_pct / groundedness_score_pct are returned as null:
        this system has NO hallucination/groundedness detector, so reporting a
        number would be fabricated. They surface as N/A in the UI by design.
    """
    from app.core.config import SessionLocal
    if not SessionLocal:
        return JSONResponse({"status": "error", "message": "DB not available"}, status_code=503)

    import asyncio
    import datetime

    def _compute() -> dict:
        from app.db.models import AgentLogs, Recommendations, Runs, Stocks
        from app.core.model_router import compute_cost, get_model_id, ModelTier
        from collections import defaultdict

        since = datetime.datetime.utcnow() - datetime.timedelta(hours=max(1, hours))
        db = SessionLocal()
        try:
            logs = db.query(AgentLogs).filter(AgentLogs.created_at >= since).all()
            recs = db.query(Recommendations).filter(Recommendations.created_at >= since).all()
            runs = db.query(Runs).filter(Runs.started_at >= since).all()
            # Recommendations has no symbol column (only stock_id FK) — build a map.
            stock_map = {s.id: s.symbol for s in db.query(Stocks.id, Stocks.symbol).all()}
        finally:
            db.close()

        # ── Per-agent breakdown ────────────────────────────────────
        agg: dict = defaultdict(lambda: {
            "invocations": 0, "failures": 0, "retries": 0,
            "conf_sum": 0.0, "conf_n": 0, "tokens": 0,
            "model_used": None, "latencies": [],
        })
        total_in = total_out = total_retries = 0
        for lg in logs:
            a = agg[lg.agent_name or "unknown"]
            a["invocations"] += 1
            if (lg.status or "").upper() == "FAILED":
                a["failures"] += 1
            rc = int(lg.retry_count or 0)
            a["retries"] += rc
            total_retries += rc
            if lg.confidence is not None:
                a["conf_sum"] += float(lg.confidence); a["conf_n"] += 1
            ti, to = int(lg.tokens_input or 0), int(lg.tokens_output or 0)
            a["tokens"] += ti + to
            total_in += ti; total_out += to
            if lg.latency_ms is not None:
                a["latencies"].append(float(lg.latency_ms))
            if lg.model_used and not a["model_used"]:
                a["model_used"] = lg.model_used

        def _pct(vals: list, p: float):
            """Nearest-rank percentile (e.g. p=0.5 → median). None if no data."""
            if not vals:
                return None
            sv = sorted(vals)
            k = max(0, min(len(sv) - 1, int(round(p * (len(sv) - 1)))))
            return round(sv[k], 1)

        agent_breakdown = []
        for name, a in sorted(agg.items()):
            inv = a["invocations"]
            agent_breakdown.append({
                "agent_name": name,
                "invocations": inv,
                "evaluations": inv,
                "failures": a["failures"],
                "success_rate": round((inv - a["failures"]) / inv * 100, 1) if inv else 0,
                "avg_confidence": round(a["conf_sum"] / a["conf_n"], 1) if a["conf_n"] else None,
                "model_used": a["model_used"],
                "retries": a["retries"],
                "total_tokens": a["tokens"],
                "p50_latency_ms": _pct(a["latencies"], 0.5),
                "p95_latency_ms": _pct(a["latencies"], 0.95),
                "tool_calls": None,        # not tracked
                "pipeline_runs": None,     # not tracked per-agent
                "hallucinations": None,    # no detector — do not fabricate
                "safety_triggers": None,   # tracked at decision level below
            })

        # ── Decision-quality eval count (same rule as /api/metrics) ─
        total_evals = len(recs)
        passed = 0
        safety_triggers = 0
        # Confidence distribution (real, from recommendation confidences).
        conf_buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
        # Debate engagement: count decisions where the debate agent actually ran.
        # NOTE: we deliberately do NOT report "debate disagreements" — the pipeline
        # runs debate on EVERY decision (graph.py: horizon_confirm → debate is
        # unconditional), and the per-decision "did the bulls/bears actually
        # dissent" flag (`debate_disagreement`) is not persisted in reasoning JSON.
        # So we surface the honest metric we DO have: how many decisions were
        # debated. Reporting "disagreements" here would be ~100% and misleading.
        debates_run = 0
        debate_seen = False
        for r in recs:
            action = (r.recommendation or "").upper()
            try:
                c = float(r.confidence) if r.confidence is not None else 0.0
            except (TypeError, ValueError):
                c = 0.0
            if c <= 1.0:
                c *= 100
            accepted = (r.validator_status or "").lower() == "accepted"
            if action == "WAIT" or (accepted and c >= 60):
                passed += 1
            # validator force-WAIT = a real safety layer blocking a bad-R:R trade
            if "forced_wait" in (r.validator_status or "").lower() or "reject" in (r.validator_status or "").lower():
                safety_triggers += 1
            # Bucket the confidence (skip rows with no confidence at all).
            if r.confidence is not None:
                if c < 20:    conf_buckets["0-20"]   += 1
                elif c < 40:  conf_buckets["20-40"]  += 1
                elif c < 60:  conf_buckets["40-60"]  += 1
                elif c < 80:  conf_buckets["60-80"]  += 1
                else:         conf_buckets["80-100"] += 1
            # Count decisions that went through the debate stage (debate_triggered).
            # This is "debates run", not "disagreements" — see note above.
            rj = r.reasoning if isinstance(r.reasoning, dict) else None
            if rj is not None:
                debate_seen = True
                if rj.get("debate_triggered") is True:
                    debates_run += 1

        cost_usd = compute_cost(get_model_id(ModelTier.ANALYSIS), total_in, total_out)

        # ── Detailed report tables (real data the UI's modal renders) ──────
        # evaluations  = recent agent-log spans
        # pipeline_runs = recent Runs
        # safety_triggers = recs whose validator rejected / forced WAIT (real safety fires)
        report_evaluations = [{
            "id": str(s.id),
            "agent_name": s.agent_name,
            "signal": s.signal or "—",
            "latency_ms": round(float(s.latency_ms), 1) if s.latency_ms is not None else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in sorted(logs, key=lambda x: x.created_at or since, reverse=True)[:50]]

        report_pipeline_runs = [{
            "id": str(r.id),
            "workflow_name": getattr(r, "workflow_name", None) or getattr(r, "run_type", None) or "analysis",
            "status": getattr(r, "status", None) or "—",
            "started_at": r.started_at.isoformat() if getattr(r, "started_at", None) else None,
        } for r in sorted(runs, key=lambda x: x.started_at or since, reverse=True)[:50]]

        report_safety = []
        for r in recs:
            vs = (r.validator_status or "").lower()
            if "reject" in vs or "forced_wait" in vs:
                issues = getattr(r, "validator_issues", None) or []
                if isinstance(issues, str):
                    issues = [issues]
                report_safety.append({
                    "id": str(r.id),
                    "symbol": stock_map.get(r.stock_id, "—"),
                    "final_confidence": float(r.confidence) if r.confidence is not None else None,
                    "validator_issues": issues,
                })

        # ── Recent spans (latest agent logs) ───────────────────────
        recent = sorted(logs, key=lambda x: x.created_at or since, reverse=True)[:25]
        recent_spans = [{
            "id": str(s.id),
            "run_id": str(s.run_id) if s.run_id else None,
            "agent_name": s.agent_name,
            "status": s.status,
            "model_used": s.model_used,
            "signal": s.signal,
            "confidence": float(s.confidence) if s.confidence is not None else None,
            "latency_ms": float(s.latency_ms) if s.latency_ms is not None else None,
            # Frontend reads tokens_in + tokens_out; also keep combined `tokens`.
            "tokens_in": int(s.tokens_input or 0),
            "tokens_out": int(s.tokens_output or 0),
            "tokens": int(s.tokens_input or 0) + int(s.tokens_output or 0),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in recent]

        return {
            "status": "success",
            "source": "db",
            "window_hours": hours,
            "hero_metrics": {
                "total_evaluations": total_evals,
                "recommendations_evaluated": total_evals,
                "pass_rate_pct": round(passed / total_evals * 100, 2) if total_evals else 0,
                "total_runs": len(runs),
                "total_retries": total_retries,
                "safety_triggers_prevented": safety_triggers,
                # Honest metric: how many decisions were debated (debate runs on
                # every decision). We do NOT report "disagreements" — that data
                # isn't persisted and would read as a misleading ~100%. None if no
                # parseable debate data in the window (don't fabricate a 0).
                "debates_run": debates_run if debate_seen else None,
                "total_decisions": total_evals,
                "hallucination_rate_pct": None,      # see groundedness via LLM judge (frontend derives from experiment)
                "groundedness_score_pct": None,      # see groundedness via LLM judge (frontend derives from experiment)
            },
            "agent_breakdown": agent_breakdown,
            "token_economics": {
                "total": total_in + total_out,
                "total_input": total_in,
                "total_output": total_out,
                "avg_tokens_per_eval": round((total_in + total_out) / total_evals) if total_evals else 0,
                "cost_usd": cost_usd,
            },
            # Real distribution of decision confidence (NOT calibration — we have no
            # resolved outcomes). Empty dict if no confidences in the window.
            "confidence_calibration": conf_buckets if any(conf_buckets.values()) else {},
            "recent_spans": recent_spans,
            "detailed_report": {
                "evaluations": report_evaluations,
                "pipeline_runs": report_pipeline_runs,
                "hallucinations": [],          # no detector — keep empty, not fabricated
                "safety_triggers": report_safety,
            },
        }

    try:
        return await asyncio.to_thread(_compute)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "ArthVest API is running"}


_DISABLED_PUBLIC_PATHS = {
    "/logs",
    "/evals",
    "/api/evals/experiment",
    "/api/improve/propose",
    "/api/improve/approve",
    "/api/improve/reject",
    "/api/arize/eval-summary",
    "/api_keys/health",
    "/connections/openai_check",
    "/analysis/test-agent",
    "/analysis/reset",
}
if not settings.ENABLE_DEV_ROUTES:
    app.routes[:] = [
        route
        for route in app.routes
        if getattr(route, "path", None) not in _DISABLED_PUBLIC_PATHS
    ]
