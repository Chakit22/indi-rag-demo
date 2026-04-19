"""Generate 150 synthetic care-journey entries for Ellie, 6y, ADHD-C + sensory.

Output: backend/data/seed.json — a list of entry objects with:
  id, source_type, date, author, title, text
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from openai import OpenAI

from app.config import OPENAI_API_KEY, LLM_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY)

OUT = Path(__file__).parent.parent.parent / "data" / "seed.json"

CHILD = {
    "name": "Ellie",
    "age": 6,
    "diagnoses": ["ADHD combined-type", "sensory processing differences"],
    "parent_name": "Maya",
    "parent_role": "mum",
    "school": "Brunswick Primary",
}

# Target distribution — realistic for a 6-month journey
TARGET = {
    "parent_log": 80,       # daily-ish entries from Maya
    "doctor_letter": 12,    # paediatrician, psychiatrist, GP
    "therapy_note": 40,     # OT, speech, psychologist
    "school_email": 18,     # teacher, learning support
}

# Buckets of themes per source — we round-robin these when prompting
THEMES = {
    "parent_log": [
        "a bad meltdown around tooth-brushing",
        "a good morning — got to school calmly",
        "stimulant medication side effect (appetite)",
        "a sensory win (new headphones at the shops)",
        "friendship drama at school pickup",
        "screen-time transition struggle",
        "a great bedtime with the new routine",
        "hyperactivity spike on a rainy day",
        "food refusal at dinner",
        "kind moment with her younger brother",
        "weekend activity sensory overload",
        "homework resistance",
        "a question for the next OT session",
    ],
    "doctor_letter": [
        "paediatrician 6-month review after starting methylphenidate",
        "psychiatrist initial assessment letter",
        "GP referral to paediatric OT",
        "paediatrician medication titration note",
        "after-hours clinic letter about acute stomach pain",
        "consultant letter to school about reasonable adjustments",
    ],
    "therapy_note": [
        "OT session focused on handwriting grip",
        "OT session on proprioceptive regulation",
        "psychology session on emotion labelling",
        "speech session on pragmatic language",
        "OT session on classroom self-regulation strategies",
        "psychology session on anxiety about sleepovers",
        "OT observation of sensory profile",
    ],
    "school_email": [
        "teacher email about a classroom meltdown",
        "learning support update on IEP progress",
        "teacher email about peer conflict at recess",
        "principal email about a good week",
        "teacher observation of focus during reading",
        "SENCO email about sensory break uptake",
    ],
}

PROMPT_TEMPLATE = """You are writing one realistic entry in the care journey of {name}, a {age}-year-old with {diagnoses}, in Melbourne, Australia. Today's date (for this entry) is {date}.

Source type: {source_type}
Author: {author}
Theme for this entry: {theme}

Write ONE entry in this JSON shape only (no commentary, no backticks):
{{
  "title": "<4-7 word title>",
  "text": "<the entry body — see length rules below>"
}}

Length rules:
- parent_log: 2-4 sentences, first-person from the mum (Maya), casual, specific, no medical jargon.
- doctor_letter: 90-140 words, formal letter prose, includes at least one concrete detail (dose, observation, plan step).
- therapy_note: 60-100 words, SOAP-ish style but loose, specific strategies named.
- school_email: 2-4 sentences, friendly but factual, signed off.

Realism rules:
- Do not invent a different diagnosis. Stay within ADHD-C + sensory.
- Use Australian spelling.
- Parent logs and school emails should sometimes be very short and mundane — the whole point is that plain top-k search drowns them out.
- NEVER write the date inside the body text — the date field is stored separately."""

AUTHORS = {
    "parent_log": ["Maya (mum)"],
    "doctor_letter": [
        "Dr A. Kostas (Paediatrician)",
        "Dr R. Meyer (Child Psychiatrist)",
        "Dr L. Tran (GP)",
    ],
    "therapy_note": [
        "Jess P. (OT)",
        "Amit S. (Psychologist)",
        "Dana K. (Speech Pathologist)",
    ],
    "school_email": [
        "Ms Harper (Year 1 teacher)",
        "Mr Doyle (Learning support)",
        "Mrs Ng (SENCO)",
    ],
}


def _random_date_between(start: str, end: str) -> str:
    from datetime import date, timedelta
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    delta = (e - s).days
    return (s + timedelta(days=random.randint(0, delta))).isoformat()


def _id(source: str, idx: int) -> str:
    prefix = {
        "parent_log": "PL",
        "doctor_letter": "DL",
        "therapy_note": "TN",
        "school_email": "SE",
    }[source]
    return f"{prefix}-{idx:03d}"


def _gen_one(source: str, idx: int) -> dict:
    theme = random.choice(THEMES[source])
    author = random.choice(AUTHORS[source])
    entry_date = _random_date_between("2025-10-19", "2026-04-18")
    prompt = PROMPT_TEMPLATE.format(
        name=CHILD["name"],
        age=CHILD["age"],
        diagnoses=" + ".join(CHILD["diagnoses"]),
        date=entry_date,
        source_type=source,
        author=author,
        theme=theme,
    )
    resp = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.85,
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    return {
        "id": _id(source, idx),
        "source_type": source,
        "date": entry_date,
        "author": author,
        "title": data.get("title", "").strip() or f"{source} entry",
        "text": data.get("text", "").strip(),
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        print(f"seed.json already exists at {OUT}, skipping generation")
        return

    all_entries: list[dict] = []
    for source, count in TARGET.items():
        print(f"Generating {count} × {source} ...")
        for i in range(1, count + 1):
            try:
                entry = _gen_one(source, i)
                all_entries.append(entry)
                if i % 10 == 0:
                    print(f"  ... {i}/{count}")
            except Exception as exc:  # noqa: BLE001
                print(f"  skip {source}#{i}: {exc}")

    all_entries.sort(key=lambda e: e["date"])
    OUT.write_text(json.dumps(all_entries, indent=2))
    print(f"Wrote {len(all_entries)} entries to {OUT}")


if __name__ == "__main__":
    main()
