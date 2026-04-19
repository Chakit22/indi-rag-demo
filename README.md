# indi for Clinicians

**The 5-minute briefing layer every new specialist needs before the first appointment.**

A clinician-side RAG demo built for [indi](https://projectindi.com) — the AI co-pilot for parents of children with complex developmental needs. This demo shows how indi's parent-generated care-journey data becomes the product's second revenue side: a grounded, cited briefing tool for clinicians onboarding new paediatric referrals.

## The problem this solves

Every new referral costs a clinician 20 minutes of the first 50-minute session catching up on a stranger's history — scrolling through PDFs, old doctor letters, therapy notes, and fragmented parent recall. The information exists. The synthesis doesn't.

indi already has the parent side. Parents log meltdowns, sleep, wins, therapy updates, school observations — an unbroken longitudinal record no EHR captures. What's missing is the layer that turns that record into a clinician-ready brief in 30 seconds.

That's what this demo is.

## Why this is indi's second revenue side

indi's moat is parent data that no other platform captures. Today that data is only monetised once — through parent subscriptions. A clinician interface monetises it a second time without asking the parent to do anything new. Clinicians already receive invites to the indi Care Team. Give them a briefing layer on top of that access and you have a two-sided platform where clinicians become a distribution channel.

1. Parent logs daily → indi accumulates the only continuous record of the child
2. Parent invites clinicians to Care Team → clinicians get read access
3. Clinician opens a referral cold → indi-for-Clinicians produces a cited brief in 30s
4. Clinician saves 20 min per intake → pushes indi to every new parent
5. More parents adopt → loop back to step 1

## The technical angle — why this query is hard

The demo ships with one loaded query, the one plain top-k cannot solve:

> *"New referral, first appointment. Give me Ellie's full clinical picture — meds, therapies, parent-reported patterns, school observations."*

Plain vector search fails because doctor letters are long, dense, and semantically similar to any clinical query — they dominate similarity scores and drown out the parent's shorter daily logs and the school's brief emails. The result: the clinician sees what the last specialist already saw, and misses the parent's real-world signal.

The fix is a **query router** that classifies intent before retrieval. For cross-source summaries it forces diversity across source types (parent logs, doctor letters, therapy notes, school emails). Every claim in the output is cited back to its source entry.

## Architecture

```
Clinician query
   │
   ▼
┌───────────────┐   ┌──────────────────────┐   ┌─────────────┐
│ Query router  │──▶│ Retrieval strategy    │──▶│ Generation  │
│ (classifier)  │   │ (diversity / top-k /  │   │ (grounded,  │
│               │   │  time-scoped)         │   │  cited)     │
└───────────────┘   └──────────────────────┘   └─────────────┘
        │                                             │
        ▼                                             ▼
   Evals layer: grounding · source coverage · latency
```

**Ported from [Chakit22/medico-legal-rag](https://github.com/Chakit22/medico-legal-rag)** — the same architecture that absorbs 7+ medical reports for legal professionals. Different domain, same hard engineering: heterogeneous documents about one person, professional user coming in cold, accuracy matters because hallucinations break trust.

## Stack

- **Backend:** Python · FastAPI · ChromaDB · OpenAI (`text-embedding-3-small` + `gpt-4o-mini`)
- **Frontend:** Next.js 14 (App Router) · Tailwind
- **Seed data:** 150 synthetic entries for Ellie, 6y, ADHD-C + sensory — parent logs, doctor letters, therapy notes, school emails
- **Deployment:** Render (backend, persistent disk for Chroma) · Vercel (frontend)

## Live demo

- **Frontend:** _(Vercel URL — updated after deploy)_
- **Backend API:** _(Render URL — updated after deploy)_
- **Source repo that inspired this:** [Chakit22/medico-legal-rag](https://github.com/Chakit22/medico-legal-rag)

## Running locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then paste your OPENAI_API_KEY
python -m app.scripts.generate_seed
python -m app.scripts.ingest
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
cp .env.local.example .env.local   # then set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000, press the hero query, see the cited brief.

## Evals

Three automated evals ship with this demo:

1. **Source coverage** — does the output cite all four source types for cross-source queries?
2. **Grounding** — is every claim traceable to a retrieved chunk?
3. **Latency** — p95 end-to-end under 5s

Run: `python -m app.evals.run_all`

## Built by Chakit Bhandari

Full-stack engineer. Previously shipped the medico-legal version of this RAG pattern for lawyers. Applying for the full-stack engineer role at indi.

- Portfolio: [Chakit22/medico-legal-rag](https://github.com/Chakit22/medico-legal-rag)
