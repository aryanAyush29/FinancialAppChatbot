"""Shared pytest fixtures / config.

Tests marked `@pytest.mark.online` are skipped automatically when GEMINI_API_KEY
is not set, so `pytest` runs cleanly with no key (offline tests only).
"""
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Make the project root importable (common.py, rag.py, ingest.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

HAS_KEY = bool(os.getenv("GEMINI_API_KEY"))


def pytest_collection_modifyitems(config, items):
    if HAS_KEY:
        return
    skip_online = pytest.mark.skip(reason="GEMINI_API_KEY not set — skipping online test")
    for item in items:
        if "online" in item.keywords:
            item.add_marker(skip_online)
