"""Singleton OpenAI client initialised from config."""

from __future__ import annotations
from typing import Optional
from openai import OpenAI
from src.config import config

_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set. Check your .env file.")
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client
