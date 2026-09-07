"""Retrieval-augmented generation core: retrieve context, then ask Gemini."""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np

from common import (
    CHAT_MODEL,
    CHUNKS_PATH,
    EMBEDDINGS_PATH,
    TOP_K,
    embed_texts,
    get_client,
)

SYSTEM_PROMPT = """\
You are "FinLit Assistant", a friendly educator that helps people understand banking and \
personal-finance concepts, terminology, and how financial products generally work.

Rules:
- Teach and explain. Define jargon in plain language, give simple examples and analogies, \
  and keep answers concise and structured.
- Ground your answer in the CONTEXT provided below. If the context does not cover the \
  question, say so plainly and give only general, widely-accepted background — do not \
  invent specifics, numbers, rates, or rules.
- Do NOT give personalised financial, investment, tax, or legal advice. Do not recommend \
  specific stocks, funds, schemes, banks, or products, and do not tell the user what they \
  personally should buy, sell, or do with their money. Instead explain the general \
  principles and trade-offs, and suggest speaking to a licensed professional for decisions.
- Many rules, rates, limits, and fees vary by country and institution and change over \
  time. Note this where relevant; lean on India-specific detail when the user's question \
  is India-specific.
- If a question is outside personal finance / banking literacy, briefly say it is outside \
  your scope.
- Never ask for or store account numbers, card numbers, PINs, OTPs, or passwords. If the \
  user shares them, warn them not to.

Format: a short direct answer first, then a few supporting bullets or a tiny example if \
helpful. Plain text / light Markdown.
"""

_DISCLAIMER = (
    "_Educational information only — not financial advice. "
    "Rules and rates vary by country and over time._"
)


@lru_cache(maxsize=1)
def _load_store():
    if not EMBEDDINGS_PATH.exists() or not CHUNKS_PATH.exists():
        raise RuntimeError(
            "Vector store not found. Run `python ingest.py` first to build "
            "store/embeddings.npy and store/chunks.json."
        )
    matrix = np.load(EMBEDDINGS_PATH)
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    return matrix, chunks


def retrieve(client, question: str, k: int = TOP_K) -> list[dict]:
    matrix, chunks = _load_store()
    q = np.array(
        embed_texts(client, [question], task_type="RETRIEVAL_QUERY")[0], dtype="float32"
    )
    scores = matrix @ q  # both sides are unit-normalised -> cosine similarity
    top = np.argsort(-scores)[:k]
    out = []
    for idx in top:
        rec = dict(chunks[int(idx)])
        rec["score"] = float(scores[int(idx)])
        out.append(rec)
    return out


def _build_context(passages: list[dict]) -> str:
    blocks = []
    for i, p in enumerate(passages, 1):
        blocks.append(f"[{i}] (source: {p['source']} — {p['topic']})\n{p['text']}")
    return "\n\n---\n\n".join(blocks)


def answer(question: str, history: list[dict] | None = None) -> dict:
    """Return {'text': str, 'sources': list[dict]}.

    history is an optional list of {'role': 'user'|'assistant', 'content': str}.
    """
    from google.genai import types

    client = get_client()
    passages = retrieve(client, question)
    context = _build_context(passages)

    convo = ""
    if history:
        for turn in history[-6:]:
            who = "User" if turn["role"] == "user" else "Assistant"
            convo += f"{who}: {turn['content']}\n"

    user_content = (
        f"CONTEXT:\n{context}\n\n"
        f"{'RECENT CONVERSATION:' + chr(10) + convo + chr(10) if convo else ''}"
        f"QUESTION: {question}"
    )

    resp = client.models.generate_content(
        model=CHAT_MODEL,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
        ),
    )
    text = (resp.text or "").strip() or (
        "Sorry, I couldn't generate an answer. Please try rephrasing."
    )
    return {"text": f"{text}\n\n{_DISCLAIMER}", "sources": passages}


if __name__ == "__main__":
    import sys

    try:  # Windows consoles default to cp1252 and can't print ₹, — etc.
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    q = " ".join(sys.argv[1:]) or "What is the difference between NEFT and RTGS?"
    result = answer(q)
    print(result["text"])
    print("\n--- sources ---")
    for s in result["sources"]:
        print(f"  {s['source']} #{s['chunk_index']}  (score {s['score']:.3f})")
