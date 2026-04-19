"""Query router: classifies a clinician's query into a retrieval strategy.

Three strategies, mirroring the medico-legal RAG pattern:

- cross_source_summary: forces diversity across all source types
  (parent_log, doctor_letter, therapy_note, school_email) so the clinician sees
  the full picture — not just what the previous specialist wrote.
- topic_focused: standard top-k over the full corpus for a specific topic
  (sleep, medication side effects, sensory regulation).
- time_scoped: filters by date range before retrieval for queries like
  "what's changed since the last appointment".
"""
from __future__ import annotations

import json
from typing import Literal
from openai import OpenAI

from app.config import OPENAI_API_KEY, LLM_MODEL

Strategy = Literal["cross_source_summary", "topic_focused", "time_scoped"]

_CLASSIFIER_PROMPT = """You classify clinician queries about a paediatric patient's care journey into exactly one retrieval strategy.

Strategies:
- cross_source_summary: the clinician wants the full clinical picture across all sources (parent logs, doctor letters, therapy notes, school emails). Typical signals: "new referral", "full picture", "catch me up", "overview", "history".
- topic_focused: the clinician is asking about ONE specific topic (sleep, a medication, a behaviour, sensory regulation). Typical signals: a single noun phrase as the subject.
- time_scoped: the clinician wants changes/events in a specific time window. Typical signals: "since last visit", "past month", "this year", "recent".

Respond with ONLY a JSON object: {"strategy": "<one of the three>", "reason": "<one short sentence>"}"""

_client = OpenAI(api_key=OPENAI_API_KEY)


def classify(query: str) -> dict:
    """Returns {"strategy": Strategy, "reason": str}."""
    resp = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _CLASSIFIER_PROMPT},
            {"role": "user", "content": query},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    strategy = data.get("strategy", "topic_focused")
    if strategy not in ("cross_source_summary", "topic_focused", "time_scoped"):
        strategy = "topic_focused"
    return {"strategy": strategy, "reason": data.get("reason", "")}
