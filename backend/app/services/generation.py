"""Grounded generation with citations. Every claim must cite [id]."""
from __future__ import annotations

from openai import OpenAI

from app.config import OPENAI_API_KEY, LLM_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY)

_BRIEF_SYSTEM = """You are a clinical briefing assistant for paediatric specialists seeing a child for the first time.

RULES (non-negotiable):
1. Every factual claim MUST cite the retrieved entry ID in square brackets at the end of the sentence, e.g. "Sleep onset has been difficult [PL-042]."
2. If the retrieved entries do not support a claim, DO NOT make it. Say so explicitly.
3. Organise the brief into these sections when relevant: Medications, Therapies, Parent-reported patterns, School observations, Red flags to ask about.
4. Keep the total brief under 250 words — it's a 30-second read, not a literature review.
5. Do not invent names, dates, diagnoses, dosages, or events. If something is missing from the retrieved entries, note the gap.

Tone: factual, concise, no filler. The clinician is walking into a room in 2 minutes."""


def generate_brief(query: str, entries: list[dict]) -> str:
    if not entries:
        return "No entries retrieved — cannot generate a grounded brief."

    context_blocks = []
    for e in entries:
        context_blocks.append(
            f"[{e['id']}] ({e['source_type']}, {e['date']}, {e.get('author', 'unknown')}) {e.get('title', '')}\n{e['text']}"
        )
    context = "\n\n".join(context_blocks)

    user = f"Clinician query:\n{query}\n\nRetrieved entries:\n{context}\n\nProduce the brief."

    resp = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _BRIEF_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""
