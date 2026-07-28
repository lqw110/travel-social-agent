"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")
    FACEBOOK_PAGE_ACCESS_TOKEN: str = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    GRAPH_API_VERSION: str = os.getenv("GRAPH_API_VERSION", "v23.0")
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"

    SUPPORTED_IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")
    MAX_IMAGES_TO_SELECT: int = 5
    MIN_RELEVANCE_SCORE: float = 6.5  # images below this score are excluded
    VISION_MODEL: str = "gpt-4o"
    TEXT_MODEL: str = "gpt-4o"


config = Config()
