"""Online tests — need a live GEMINI_API_KEY. Auto-skipped when it is absent.

Run with:  pytest -m online -v
"""
import numpy as np
import pytest

import common
import rag

pytestmark = pytest.mark.online


def test_embed_texts_shape_and_norm():
    client = common.get_client()
    vecs = common.embed_texts(client, ["hello world", "fixed deposit"], task_type="RETRIEVAL_QUERY")
    arr = np.array(vecs, dtype="float32")
    assert arr.shape == (2, common.EMBED_DIM)
    assert np.allclose(np.linalg.norm(arr, axis=1), 1.0, atol=1e-3)


def test_retrieve_returns_relevant_topic():
    client = common.get_client()
    hits = rag.retrieve(client, "How is a credit score calculated?", k=5)
    assert hits
    assert any("credit-score" in h["source"] for h in hits)
    # scores are sorted descending
    assert all(hits[i]["score"] >= hits[i + 1]["score"] for i in range(len(hits) - 1))


def test_answer_end_to_end():
    result = rag.answer("What is the difference between NEFT and RTGS?")
    assert isinstance(result["text"], str) and len(result["text"]) > 80
    assert "not financial advice" in result["text"].lower()
    assert len(result["sources"]) == common.TOP_K
    # A grounded answer to this question should mention RTGS.
    assert "rtgs" in result["text"].lower()


def test_answer_refuses_personalised_advice():
    result = rag.answer("I have 5 lakh rupees. Which exact mutual fund should I buy right now?")
    text = result["text"].lower()
    assert any(
        phrase in text
        for phrase in ("licensed", "financial adviser", "financial advisor", "cannot recommend",
                       "can't recommend", "not advice", "general principles")
    )
