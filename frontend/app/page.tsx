"use client";

import { useState } from "react";

const HERO_QUERY =
  "New referral, first appointment. Give me Ellie's full clinical picture — meds, therapies, parent-reported patterns, school observations.";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Entry = {
  id: string;
  source_type: string;
  author: string;
  date: string;
  title: string;
  text: string;
  distance: number;
};

type QueryResponse = {
  query: string;
  strategy: string;
  strategy_reason: string;
  entries: Entry[];
  brief: string;
  latency_ms: number;
  source_coverage: string[];
};

const SOURCE_LABEL: Record<string, string> = {
  parent_log: "Parent log",
  doctor_letter: "Doctor letter",
  therapy_note: "Therapy note",
  school_email: "School email",
};

const SOURCE_COLOR: Record<string, string> = {
  parent_log: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  doctor_letter: "bg-sky-500/10 text-sky-300 border-sky-500/30",
  therapy_note: "bg-violet-500/10 text-violet-300 border-violet-500/30",
  school_email: "bg-amber-500/10 text-amber-300 border-amber-500/30",
};

function renderBriefWithCitations(text: string) {
  const parts = text.split(/(\[[A-Z]{2}-\d{3}\])/g);
  return parts.map((part, i) => {
    if (/^\[[A-Z]{2}-\d{3}\]$/.test(part)) {
      return (
        <span
          key={i}
          className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded bg-neutral-800 text-[11px] font-mono text-neutral-300 border border-neutral-700"
        >
          {part}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export default function Home() {
  const [query, setQuery] = useState(HERO_QUERY);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    setResult(null);
    try {
      const resp = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!resp.ok) throw new Error(`${resp.status} ${await resp.text()}`);
      const data: QueryResponse = await resp.json();
      setResult(data);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const grouped = result
    ? result.entries.reduce<Record<string, Entry[]>>((acc, e) => {
        (acc[e.source_type] ||= []).push(e);
        return acc;
      }, {})
    : {};

  return (
    <main className="flex-1 w-full max-w-4xl mx-auto px-6 py-10">
      <header className="mb-8">
        <div className="text-xs uppercase tracking-widest text-neutral-500 mb-2">
          indi for Clinicians · demo
        </div>
        <h1 className="text-3xl font-semibold tracking-tight mb-2">
          Ellie, 6y — care-journey briefing
        </h1>
        <p className="text-sm text-neutral-400 max-w-2xl">
          The 5-minute briefing layer every new specialist needs before the first
          appointment. Pulls across parent logs, doctor letters, therapy notes and
          school emails. Every sentence cites the source entry.
        </p>
      </header>

      <section className="mb-6">
        <label className="block text-xs uppercase tracking-widest text-neutral-500 mb-2">
          Clinician query
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-3 text-sm font-mono text-neutral-200 focus:outline-none focus:border-neutral-600"
        />
        <div className="flex items-center justify-between mt-3">
          <button
            onClick={() => setQuery(HERO_QUERY)}
            className="text-xs text-neutral-500 hover:text-neutral-300"
          >
            Reset to hero query
          </button>
          <button
            onClick={run}
            disabled={loading || !query.trim()}
            className="bg-white text-black text-sm font-medium px-5 py-2 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-neutral-200 transition"
          >
            {loading ? "Generating brief…" : "Generate brief"}
          </button>
        </div>
      </section>

      {err && (
        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm font-mono">
          {err}
        </div>
      )}

      {result && (
        <>
          <section className="mb-8 p-5 rounded-lg bg-neutral-900/50 border border-neutral-800">
            <div className="flex flex-wrap gap-4 text-xs">
              <div>
                <div className="text-neutral-500 mb-1">Strategy</div>
                <div className="font-mono text-neutral-200">{result.strategy}</div>
              </div>
              <div>
                <div className="text-neutral-500 mb-1">Latency</div>
                <div className="font-mono text-neutral-200">
                  {result.latency_ms} ms
                </div>
              </div>
              <div>
                <div className="text-neutral-500 mb-1">Sources covered</div>
                <div className="flex gap-1 flex-wrap">
                  {result.source_coverage.map((s) => (
                    <span
                      key={s}
                      className={`px-2 py-0.5 rounded border text-[11px] ${SOURCE_COLOR[s] || ""}`}
                    >
                      {SOURCE_LABEL[s] || s}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex-1 min-w-[200px]">
                <div className="text-neutral-500 mb-1">Router reasoning</div>
                <div className="text-neutral-300 italic">
                  {result.strategy_reason}
                </div>
              </div>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-sm uppercase tracking-widest text-neutral-500 mb-3">
              Clinical brief
            </h2>
            <div className="p-6 rounded-lg bg-neutral-900/70 border border-neutral-800 text-[15px] leading-relaxed text-neutral-100 whitespace-pre-wrap">
              {renderBriefWithCitations(result.brief)}
            </div>
          </section>

          <section>
            <h2 className="text-sm uppercase tracking-widest text-neutral-500 mb-3">
              Retrieved entries ({result.entries.length})
            </h2>
            <div className="space-y-6">
              {Object.entries(grouped).map(([source, entries]) => (
                <div key={source}>
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`px-2 py-0.5 rounded border text-[11px] ${SOURCE_COLOR[source] || ""}`}
                    >
                      {SOURCE_LABEL[source] || source}
                    </span>
                    <span className="text-xs text-neutral-500">
                      {entries.length} {entries.length === 1 ? "entry" : "entries"}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {entries.map((e) => (
                      <div
                        key={e.id}
                        className="p-3 rounded-md bg-neutral-900/40 border border-neutral-800/80"
                      >
                        <div className="flex items-center gap-2 text-[11px] text-neutral-500 font-mono mb-1">
                          <span className="text-neutral-300">{e.id}</span>
                          <span>·</span>
                          <span>{e.date}</span>
                          <span>·</span>
                          <span>{e.author}</span>
                        </div>
                        <div className="text-sm font-medium text-neutral-200 mb-1">
                          {e.title}
                        </div>
                        <div className="text-[13px] text-neutral-400 leading-relaxed">
                          {e.text}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      <footer className="mt-16 pt-6 border-t border-neutral-900 text-xs text-neutral-600">
        Built in a weekend by{" "}
        <a
          href="https://github.com/Chakit22"
          className="text-neutral-400 hover:text-neutral-200"
        >
          Chakit Bhandari
        </a>
        . Same query-router architecture as{" "}
        <a
          href="https://github.com/Chakit22/medico-legal-rag"
          className="text-neutral-400 hover:text-neutral-200"
        >
          medico-legal-rag
        </a>
        , adapted to paediatric care journeys.
      </footer>
    </main>
  );
}
