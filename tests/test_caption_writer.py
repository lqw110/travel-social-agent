"""Tests for caption writer (stub — requires OpenAI key for integration tests)."""

import pytest  # noqa: F401


def test_caption_writer_stub() -> None:
    """Placeholder — replace with a real test once OPENAI_API_KEY is available."""
    pytest.importorskip("openai", reason="openai package not installed")
    from src.agents.caption_writer import caption_generation_node
    assert callable(caption_generation_node)
