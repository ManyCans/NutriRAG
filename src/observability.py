"""
Lightweight tracing + cost tracking for NutriRAG.

No OpenTelemetry / external collector needed at this scale — this is a
single SQLite table that records one row per traced span. It's enough to
compute p50/p95 latency per stage, per-request cost, and to feed the eval
harness's regression report.

Usage:
    from src.observability import traced, log_llm_usage, get_trace_db

    @traced("retrieve")
    def retrieve(query, k=4):
        ...

Each call writes a row: (request_id, span, duration_ms, timestamp, meta_json)
request_id ties multiple spans from the same end-to-end call together, so you
can reconstruct "for this one query, retrieval took 40ms and generation took
900ms" rather than just aggregate numbers.
"""
from __future__ import annotations

import contextvars
import functools
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Callable

DB_PATH = Path(__file__).parent.parent / "data" / "traces.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Ties spans emitted during one logical request together without threading
# a request_id argument through every function signature.
_current_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_request_id", default=None
)


def _init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                span_name TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                timestamp REAL NOT NULL,
                meta_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                cost_usd REAL,
                timestamp REAL NOT NULL
            )
            """
        )


_init_db()


def new_request_id() -> str:
    """Call once at the top of a request (e.g. in answer_query or the
    Streamlit handler) to group every span from that call together."""
    rid = str(uuid.uuid4())[:8]
    _current_request_id.set(rid)
    return rid


def _record_span(span_name: str, duration_ms: float, meta: dict | None = None) -> None:
    rid = _current_request_id.get() or "unbound"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO spans (request_id, span_name, duration_ms, timestamp, meta_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (rid, span_name, duration_ms, time.time(), json.dumps(meta or {})),
        )


def traced(span_name: str) -> Callable:
    """Decorator: wraps a function, records its wall-clock duration as a
    named span. Works on any function; doesn't change its return value."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = fn(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            _record_span(span_name, duration_ms)
            return result

        return wrapper

    return decorator


# --- Cost tracking -----------------------------------------------------
# Per-1M-token USD pricing. Verify current rates at console.groq.com/docs
# before relying on this for anything beyond relative comparison — Groq's
# published per-token pricing for some models has moved to
# enterprise/contact-sales at times, so don't hardcode this into a bill.
GROQ_PRICING_PER_1M = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
}


def log_llm_usage(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Call after an LLM API response. Returns the estimated cost in USD
    and logs it tied to the current request_id."""
    rates = GROQ_PRICING_PER_1M.get(model, {"input": 0.0, "output": 0.0})
    cost_usd = (
        prompt_tokens * rates["input"] / 1_000_000
        + completion_tokens * rates["output"] / 1_000_000
    )
    rid = _current_request_id.get() or "unbound"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO llm_usage (request_id, model, prompt_tokens, completion_tokens, cost_usd, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (rid, model, prompt_tokens, completion_tokens, cost_usd, time.time()),
        )
    return cost_usd


def get_trace_db() -> Path:
    return DB_PATH


# --- Percentile / summary reporting ------------------------------------
def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(round((p / 100) * (len(values) - 1)))
    return values[idx]


def summarize(since_ts: float | None = None) -> dict[str, Any]:
    """Read back all spans + usage and compute p50/p95 latency per span
    name, plus total and average cost. This is what the eval script and
    any dashboard panel should call."""
    with sqlite3.connect(DB_PATH) as conn:
        span_rows = conn.execute(
            "SELECT span_name, duration_ms FROM spans"
            + (" WHERE timestamp >= ?" if since_ts else ""),
            (since_ts,) if since_ts else (),
        ).fetchall()
        usage_rows = conn.execute(
            "SELECT cost_usd FROM llm_usage"
            + (" WHERE timestamp >= ?" if since_ts else ""),
            (since_ts,) if since_ts else (),
        ).fetchall()

    by_span: dict[str, list[float]] = {}
    for name, dur in span_rows:
        by_span.setdefault(name, []).append(dur)

    latency_summary = {
        name: {
            "p50_ms": round(percentile(durs, 50), 1),
            "p95_ms": round(percentile(durs, 95), 1),
            "count": len(durs),
        }
        for name, durs in by_span.items()
    }

    costs = [c for (c,) in usage_rows]
    cost_summary = {
        "total_usd": round(sum(costs), 6),
        "avg_usd_per_request": round(sum(costs) / len(costs), 6) if costs else 0.0,
        "num_requests": len(costs),
    }

    return {"latency": latency_summary, "cost": cost_summary}
