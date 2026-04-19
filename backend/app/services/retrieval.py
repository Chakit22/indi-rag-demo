"""Retrieval strategies. Each takes a query and returns a list of retrieved entries.

The whole point of the router is here: a cross_source_summary MUST return entries
from every source type. Plain top-k does not do that because doctor letters are
longer and more semantically dense than parent logs or school emails, so they
dominate similarity — and the clinician sees only what the last specialist saw.
"""
from __future__ import annotations

import chromadb
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHROMA_PATH, EMBED_MODEL, COLLECTION_NAME

SOURCE_TYPES = ["parent_log", "doctor_letter", "therapy_note", "school_email"]

_openai = OpenAI(api_key=OPENAI_API_KEY)
_chroma = chromadb.PersistentClient(path=CHROMA_PATH)


def _embed(text: str) -> list[float]:
    resp = _openai.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def _collection():
    return _chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _hit_to_entry(doc: str, meta: dict, entry_id: str, distance: float) -> dict:
    return {
        "id": entry_id,
        "source_type": meta.get("source_type"),
        "author": meta.get("author"),
        "date": meta.get("date"),
        "title": meta.get("title"),
        "text": doc,
        "distance": distance,
    }


def topic_focused(query: str, k: int = 8) -> list[dict]:
    """Standard top-k over the full corpus."""
    col = _collection()
    emb = _embed(query)
    res = col.query(query_embeddings=[emb], n_results=k)
    out = []
    for doc, meta, entry_id, dist in zip(
        res["documents"][0], res["metadatas"][0], res["ids"][0], res["distances"][0]
    ):
        out.append(_hit_to_entry(doc, meta, entry_id, dist))
    return out


def cross_source_summary(query: str, per_source: int = 3) -> list[dict]:
    """Forces retrieval from every source type so nothing gets drowned out."""
    col = _collection()
    emb = _embed(query)
    all_hits: list[dict] = []
    for source in SOURCE_TYPES:
        res = col.query(
            query_embeddings=[emb],
            n_results=per_source,
            where={"source_type": source},
        )
        if not res["ids"] or not res["ids"][0]:
            continue
        for doc, meta, entry_id, dist in zip(
            res["documents"][0], res["metadatas"][0], res["ids"][0], res["distances"][0]
        ):
            all_hits.append(_hit_to_entry(doc, meta, entry_id, dist))
    return all_hits


def time_scoped(query: str, since_iso: str | None = None, k: int = 10) -> list[dict]:
    """Retrieval filtered by date >= since_iso (YYYY-MM-DD). Falls back to topic if no date."""
    if not since_iso:
        return topic_focused(query, k=k)
    col = _collection()
    emb = _embed(query)
    res = col.query(
        query_embeddings=[emb],
        n_results=k,
        where={"date": {"$gte": since_iso}},
    )
    out = []
    if not res["ids"] or not res["ids"][0]:
        return out
    for doc, meta, entry_id, dist in zip(
        res["documents"][0], res["metadatas"][0], res["ids"][0], res["distances"][0]
    ):
        out.append(_hit_to_entry(doc, meta, entry_id, dist))
    return out
