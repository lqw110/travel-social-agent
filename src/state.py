"""Shared state definition for the LangGraph agent workflow."""

from typing import Any, Optional
from typing_extensions import TypedDict


class ImageCandidate(TypedDict):
    path: str
    filename: str
    size_bytes: int
    width: Optional[int]
    height: Optional[int]


class RankedImage(TypedDict):
    path: str
    filename: str
    relevance_score: float  # 1–10
    reason: str


class StoryAnalysis(TypedDict):
    location: str
    main_event: str
    emotional_tone: str
    key_objects_scenes: list[str]
    suggested_facebook_tone: str


class AgentState(TypedDict):
    # Inputs
    story_text: str
    photo_folder: str

    # Pipeline data
    image_candidates: list[ImageCandidate]
    story_analysis: Optional[StoryAnalysis]
    ranked_images: list[RankedImage]
    selected_images: list[RankedImage]

    # Output
    caption_draft: str
    final_caption: str
    approval_status: str  # "pending" | "approved" | "rejected"
    facebook_post_result: Optional[dict[str, Any]]

    # Meta
    errors: list[str]
    dry_run: bool
