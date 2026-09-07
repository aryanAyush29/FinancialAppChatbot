"""Build the vector store from knowledge_base/*.md.

Run once (and again whenever you edit the knowledge base):

    python ingest.py

Outputs store/embeddings.npy and store/chunks.json, which the app loads at runtime.
Requires GEMINI_API_KEY in your environment or .env file.
"""
from __future__ import annotations

import json
import re
import sys

import numpy as np

from common import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKS_PATH,
    EMBEDDINGS_PATH,
    EMBED_MODEL,
    KB_DIR,
    STORE_DIR,
    embed_texts,
    get_client,
)

BATCH = 50  # texts per embedding request


def split_into_chunks(text: str) -> list[str]:
    """Split on blank lines, then pack paragraphs into overlapping windows."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paras:
        if len(buf) + len(para) + 2 <= CHUNK_SIZE:
            buf = f"{buf}\n\n{para}" if buf else para
        else:
            if buf:
                chunks.append(buf)
            if len(para) > CHUNK_SIZE:
                # Hard-wrap an oversized paragraph.
                for i in range(0, len(para), CHUNK_SIZE - CHUNK_OVERLAP):
                    chunks.append(para[i : i + CHUNK_SIZE])
                buf = ""
            else:
                buf = para
    if buf:
        chunks.append(buf)

    # Add a little overlap between consecutive chunks for context continuity.
    if CHUNK_OVERLAP and len(chunks) > 1:
        overlapped = [chunks[0]]
        for prev, cur in zip(chunks, chunks[1:]):
            tail = prev[-CHUNK_OVERLAP:]
            overlapped.append(f"...{tail}\n\n{cur}")
        chunks = overlapped
    return chunks


def main() -> None:
    md_files = sorted(KB_DIR.glob("*.md"))
    if not md_files:
        sys.exit(f"No markdown files found in {KB_DIR}")

    records: list[dict] = []
    for path in md_files:
        raw = path.read_text(encoding="utf-8")
        topic = path.stem.replace("-", " ").title()
        for i, chunk in enumerate(split_into_chunks(raw)):
            records.append(
                {"source": path.name, "topic": topic, "chunk_index": i, "text": chunk}
            )

    print(f"{len(md_files)} files -> {len(records)} chunks. Embedding with {EMBED_MODEL} ...")

    client = get_client()
    all_vecs: list[list[float]] = []
    for start in range(0, len(records), BATCH):
        batch = [r["text"] for r in records[start : start + BATCH]]
        all_vecs.extend(embed_texts(client, batch, task_type="RETRIEVAL_DOCUMENT"))
        print(f"  embedded {min(start + BATCH, len(records))}/{len(records)}")

    matrix = np.array(all_vecs, dtype="float32")

    STORE_DIR.mkdir(exist_ok=True)
    np.save(EMBEDDINGS_PATH, matrix)
    CHUNKS_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved {EMBEDDINGS_PATH} {matrix.shape} and {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
