"""Offline tests — no API key or network needed.

They cover the plumbing: chunking, config sanity, the vector store on disk,
prompt guardrails, and the retrieval ranking maths (with embeddings mocked).
"""
import json

import numpy as np
import pytest

import common
import ingest
import rag


# --- chunking -------------------------------------------------------------

def test_split_into_chunks_basic():
    text = "\n\n".join(f"Paragraph number {i} with some words." for i in range(30))
    chunks = ingest.split_into_chunks(text)
    assert chunks, "expected at least one chunk"
    assert all(isinstance(c, str) and c.strip() for c in chunks)
    # Nothing wildly larger than the configured window (+ overlap prefix).
    assert max(len(c) for c in chunks) <= common.CHUNK_SIZE + common.CHUNK_OVERLAP + 50


def test_split_into_chunks_adds_overlap_prefix():
    text = "\n\n".join(f"{'word ' * 60}block {i}" for i in range(10))
    chunks = ingest.split_into_chunks(text)
    assert len(chunks) > 1
    assert chunks[1].startswith("..."), "chunks after the first should carry an overlap prefix"


def test_every_knowledge_base_file_produces_chunks():
    md_files = sorted(common.KB_DIR.glob("*.md"))
    assert len(md_files) >= 5
    for path in md_files:
        assert ingest.split_into_chunks(path.read_text(encoding="utf-8"))


# --- config -------------------------------------------------------------

def test_config_values_are_sane():
    assert common.EMBED_DIM > 0
    assert common.TOP_K >= 1
    assert common.CHAT_MODEL and common.EMBED_MODEL


# --- vector store on disk ---------------------------------------------------

def _store_exists():
    return common.EMBEDDINGS_PATH.exists() and common.CHUNKS_PATH.exists()


@pytest.mark.skipif(not _store_exists(), reason="run `python ingest.py` first")
def test_store_matrix_matches_chunks():
    matrix = np.load(common.EMBEDDINGS_PATH)
    chunks = json.loads(common.CHUNKS_PATH.read_text(encoding="utf-8"))
    assert matrix.shape[0] == len(chunks)
    assert matrix.shape[1] == common.EMBED_DIM
    # rows should be unit-normalised
    norms = np.linalg.norm(matrix, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)


@pytest.mark.skipif(not _store_exists(), reason="run `python ingest.py` first")
def test_chunk_records_have_expected_fields():
    chunks = json.loads(common.CHUNKS_PATH.read_text(encoding="utf-8"))
    for rec in chunks:
        assert {"source", "topic", "chunk_index", "text"} <= rec.keys()


# --- guardrails -------------------------------------------------------------

def test_system_prompt_has_guardrails():
    p = rag.SYSTEM_PROMPT.lower()
    assert "not give personalised" in p or "not give personalized" in p
    assert "context" in p
    assert "otp" in p  # credential-safety clause


def test_build_context_is_numbered_and_cites_source():
    passages = [
        {"source": "a.md", "topic": "A", "text": "alpha"},
        {"source": "b.md", "topic": "B", "text": "beta"},
    ]
    ctx = rag._build_context(passages)
    assert "[1]" in ctx and "[2]" in ctx
    assert "a.md" in ctx and "beta" in ctx


# --- retrieval ranking (embeddings mocked) --------------------------------

def test_retrieve_ranks_by_cosine(monkeypatch):
    # Fake store: 3 orthogonal-ish rows.
    fake_matrix = np.eye(3, common.EMBED_DIM, dtype="float32")
    fake_chunks = [
        {"source": "s0.md", "topic": "T0", "chunk_index": 0, "text": "row zero"},
        {"source": "s1.md", "topic": "T1", "chunk_index": 1, "text": "row one"},
        {"source": "s2.md", "topic": "T2", "chunk_index": 2, "text": "row two"},
    ]
    monkeypatch.setattr(rag, "_load_store", lambda: (fake_matrix, fake_chunks))
    # Query vector closest to row 1.
    qvec = np.zeros(common.EMBED_DIM, dtype="float32")
    qvec[1] = 1.0
    monkeypatch.setattr(rag, "embed_texts", lambda *a, **k: [qvec.tolist()])

    hits = rag.retrieve(client=None, question="anything", k=2)
    assert hits[0]["source"] == "s1.md"
    assert hits[0]["score"] == pytest.approx(1.0, abs=1e-4)
    assert len(hits) == 2
