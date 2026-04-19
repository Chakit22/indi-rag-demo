"""Three automated evals — run offline against the live retrieval stack.

1. source_coverage: cross_source_summary query must return entries from all 4 source types.
2. grounding: every [ID] cited in the brief must resolve to a retrieved entry.
3. latency: p95 latency under 5s across a small eval set.
"""
from __future__ import annotations

import re
import statistics
import time

from app.services import router as query_router
from app.services import retrieval
from app.services import generation

HERO_QUERY = (
    "New referral, first appointment. Give me Ellie's full clinical picture — "
    "meds, therapies, parent-reported patterns, school observations."
)

EVAL_QUERIES = [
    HERO_QUERY,
    "How's Ellie's sleep been?",
    "Summarise medication changes in the past three months.",
    "What sensory triggers come up most often at school?",
    "Catch me up on Ellie's therapy progress.",
]

CITE_RE = re.compile(r"\[([A-Z]{2}-\d{3})\]")


def _run_pipeline(q: str) -> tuple[dict, list[dict], str, float]:
    t0 = time.time()
    routing = query_router.classify(q)
    if routing["strategy"] == "cross_source_summary":
        entries = retrieval.cross_source_summary(q)
    elif routing["strategy"] == "time_scoped":
        entries = retrieval.time_scoped(q)
    else:
        entries = retrieval.topic_focused(q)
    brief = generation.generate_brief(q, entries)
    latency = time.time() - t0
    return routing, entries, brief, latency


def eval_source_coverage() -> dict:
    routing, entries, _, _ = _run_pipeline(HERO_QUERY)
    sources = {e["source_type"] for e in entries}
    required = {"parent_log", "doctor_letter", "therapy_note", "school_email"}
    passed = required.issubset(sources)
    return {
        "name": "source_coverage",
        "passed": passed,
        "strategy": routing["strategy"],
        "got_sources": sorted(sources),
        "missing": sorted(required - sources),
    }


def eval_grounding() -> dict:
    _, entries, brief, _ = _run_pipeline(HERO_QUERY)
    retrieved_ids = {e["id"] for e in entries}
    cited_ids = set(CITE_RE.findall(brief))
    orphans = cited_ids - retrieved_ids
    passed = len(orphans) == 0 and len(cited_ids) > 0
    return {
        "name": "grounding",
        "passed": passed,
        "cited": len(cited_ids),
        "retrieved": len(retrieved_ids),
        "orphans": sorted(orphans),
    }


def eval_latency() -> dict:
    latencies: list[float] = []
    for q in EVAL_QUERIES:
        _, _, _, lat = _run_pipeline(q)
        latencies.append(lat)
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 2 else latencies[0]
    return {
        "name": "latency",
        "passed": p95 < 5.0,
        "p95_seconds": round(p95, 2),
        "n": len(latencies),
    }


def main() -> None:
    results = [eval_source_coverage(), eval_grounding(), eval_latency()]
    print("=== Eval results ===")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['name']}: {r}")
    if not all(r["passed"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
