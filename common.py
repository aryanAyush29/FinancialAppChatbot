"""Shared configuration and helpers for the financial-literacy chatbot."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
KB_DIR = ROOT / "knowledge_base"
STORE_DIR = ROOT / "store"
EMBEDDINGS_PATH = STORE_DIR / "embeddings.npy"
CHUNKS_PATH = STORE_DIR / "chunks.json"

CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))
TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# Chunking parameters (characters, not tokens — simple and good enough here).
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def get_api_key() -> str:
    """Return the Gemini API key from the environment or Streamlit secrets."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:  # Streamlit Cloud stores it in st.secrets
            import streamlit as st

            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            key = None
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Create a free key at "
            "https://aistudio.google.com/app/apikey and put it in a .env file "
            "(local) or in the app's Secrets (Streamlit Cloud)."
        )
    return key


def get_client():
    """Create a Google GenAI client."""
    from google import genai

    return genai.Client(api_key=get_api_key())


def embed_texts(client, texts: list[str], *, task_type: str) -> "list[list[float]]":
    """Embed a list of texts and return unit-normalised vectors.

    task_type is "RETRIEVAL_DOCUMENT" when indexing the knowledge base and
    "RETRIEVAL_QUERY" when embedding a user question.
    """
    import numpy as np
    from google.genai import types

    try:
        resp = client.models.embed_content(
            model=EMBED_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBED_DIM,
            ),
        )
    except Exception:
        # Some embedding models reject task_type / output_dimensionality.
        resp = client.models.embed_content(model=EMBED_MODEL, contents=texts)

    vecs = np.array([e.values for e in resp.embeddings], dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vecs / norms).tolist()
