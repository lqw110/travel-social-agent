"""Agent nodes: scan images, score relevance, select the best ones."""

import base64
import logging
from pathlib import Path

from src.config import config
from src.services.openai_client import get_openai_client
from src.state import AgentState, ImageCandidate, RankedImage
from src.tools.image_tools import scan_local_images, select_best_images, load_image_as_jpeg_bytes

logger = logging.getLogger(__name__)

_RELEVANCE_PROMPT_PATH = (
    Path(__file__).parent.parent / "prompts" / "image_relevance_prompt.md"
)


# ---------------------------------------------------------------------------
# Core tool functions
# ---------------------------------------------------------------------------

def score_image_relevance(
    image_path: str,
    story_analysis: dict,
    story_text: str,
) -> RankedImage:
    """Use the vision model to score how relevant an image is to the story.

    Args:
        image_path: Absolute path to the image file.
        story_analysis: Structured story metadata from analyze_story.
        story_text: Original story text for additional context.

    Returns:
        RankedImage with relevance_score (1–10) and a brief reason.
    """
    system_prompt = _RELEVANCE_PROMPT_PATH.read_text()
    client = get_openai_client()

    # load_image_as_jpeg_bytes handles HEIC → JPEG conversion automatically
    image_data = load_image_as_jpeg_bytes(image_path)
    b64 = base64.b64encode(image_data).decode()
    mime = "image/jpeg"

    context = (
        f"Story: {story_text}\n\n"
        f"Location: {story_analysis.get('location')}\n"
        f"Main event: {story_analysis.get('main_event')}\n"
        f"Emotional tone: {story_analysis.get('emotional_tone')}\n"
        f"Key objects/scenes to look for: {', '.join(story_analysis.get('key_objects_scenes', []))}"
    )

    response = client.chat.completions.create(
        model=config.VISION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": context},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            },
        ],
        max_tokens=256,
    )

    raw = response.choices[0].message.content or ""
    score, reason = _parse_score_response(raw)
    filename = Path(image_path).name
    logger.info("  %s → score %.1f", filename, score)
    return RankedImage(
        path=image_path,
        filename=filename,
        relevance_score=score,
        reason=reason,
    )


def _parse_score_response(text: str) -> tuple[float, str]:
    """Extract numeric score and reason from the model's free-text reply."""
    import re

    score = 5.0
    reason = text.strip()
    match = re.search(r"score[:\s]+([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if match:
        score = min(10.0, max(1.0, float(match.group(1))))
    # Reason is everything after the score line
    reason_match = re.search(r"reason[:\s]+(.+)", text, re.IGNORECASE | re.DOTALL)
    if reason_match:
        reason = reason_match.group(1).strip()
    return score, reason


# ---------------------------------------------------------------------------
# LangGraph nodes
# ---------------------------------------------------------------------------

def photo_scan_node(state: AgentState) -> AgentState:
    """LangGraph node: scan the photo folder and populate image_candidates."""
    try:
        candidates: list[ImageCandidate] = scan_local_images(state["photo_folder"])
        return {**state, "image_candidates": candidates}
    except Exception as exc:
        logger.error("photo_scan_node failed: %s", exc)
        return {**state, "errors": state["errors"] + [str(exc)]}


def photo_relevance_node(state: AgentState) -> AgentState:
    """LangGraph node: score each candidate image for story relevance."""
    analysis = state.get("story_analysis")
    if not analysis:
        err = "story_analysis missing — cannot score images"
        return {**state, "errors": state["errors"] + [err]}

    ranked: list[RankedImage] = []
    for candidate in state["image_candidates"]:
        try:
            ranked_img = score_image_relevance(
                candidate["path"], dict(analysis), state["story_text"]
            )
            ranked.append(ranked_img)
        except Exception as exc:
            logger.warning("Failed to score %s: %s", candidate["filename"], exc)

    return {**state, "ranked_images": ranked}


def photo_selection_node(state: AgentState) -> AgentState:
    """LangGraph node: pick the best images from the ranked list."""
    selected = select_best_images(
        state["ranked_images"],
        max_images=config.MAX_IMAGES_TO_SELECT,
        min_score=config.MIN_RELEVANCE_SCORE,
    )
    return {**state, "selected_images": selected}
