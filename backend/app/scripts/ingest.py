"""Ingest data/seed.json into Chroma. Idempotent — drops and rebuilds the collection."""
from __future__ import annotations

import json
from pathlib import Path

import chromadb
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHROMA_PATH, EMBED_MODEL, COLLECTION_NAME

SEED = Path(__file__).parent.parent.parent / "data" / "seed.json"


def _embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def main() -> None:
    if not SEED.exists():
        raise SystemExit(f"No seed file at {SEED}. Run generate_seed first.")

    entries = json.loads(SEED.read_text())
    print(f"Loaded {len(entries)} entries from {SEED}")

    openai = OpenAI(api_key=OPENAI_API_KEY)
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        chroma.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    col = chroma.create_collection(name=COLLECTION_NAME)

    batch_size = 50
    for i in range(0, len(entries), batch_size):
        batch = entries[i : i + batch_size]
        ids = [e["id"] for e in batch]
        docs = [f"{e.get('title', '')}\n{e['text']}" for e in batch]
        metas = [
            {
                "source_type": e["source_type"],
                "date": e["date"],
                "author": e.get("author", ""),
                "title": e.get("title", ""),
            }
            for e in batch
        ]
        embs = _embed_batch(openai, docs)
        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        print(f"  embedded {i + len(batch)}/{len(entries)}")

    print(f"Ingested {col.count()} documents into '{COLLECTION_NAME}' at {CHROMA_PATH}")


if __name__ == "__main__":
    main()
