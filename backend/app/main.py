"""FastAPI entrypoint. One main endpoint: POST /query."""
from __future__ import annotations

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services import router as query_router
from app.services import retrieval
from app.services import generation

app = FastAPI(title="indi for Clinicians — briefing layer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    since: str | None = None


class QueryResponse(BaseModel):
    query: str
    strategy: str
    strategy_reason: str
    entries: list[dict]
    brief: str
    latency_ms: int
    source_coverage: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    t0 = time.time()
    routing = query_router.classify(req.query)
    strategy = routing["strategy"]

    if strategy == "cross_source_summary":
        entries = retrieval.cross_source_summary(req.query)
    elif strategy == "time_scoped":
        entries = retrieval.time_scoped(req.query, since_iso=req.since)
    else:
        entries = retrieval.topic_focused(req.query)

    brief = generation.generate_brief(req.query, entries)
    coverage = sorted({e["source_type"] for e in entries if e.get("source_type")})
    latency = int((time.time() - t0) * 1000)

    return QueryResponse(
        query=req.query,
        strategy=strategy,
        strategy_reason=routing["reason"],
        entries=entries,
        brief=brief,
        latency_ms=latency,
        source_coverage=coverage,
    )


@app.get("/")
def root() -> dict:
    return {
        "name": "indi for Clinicians",
        "hint": "POST /query with {\"query\": \"...\"}",
    }
