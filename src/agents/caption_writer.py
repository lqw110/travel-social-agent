"""Agent node: generate a warm, natural Facebook caption."""

import logging
from pathlib import Path

from src.config import config
from src.services.openai_client import get_openai_client
from src.state import AgentState, RankedImage, StoryAnalysis

logger = logging.getLogger(__name__)

_CAPTION_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "caption_prompt.md"


def generate_facebook_caption(
    story_text: str,
    selected_images: list[RankedImage],
    story_analysis: StoryAnalysis,
) -> str:
    """Create a natural Facebook caption from the story and selected images.

    The tone should be personal and warm — not influencer-ish or generic.
    Hashtags are avoided unless they add real value.

    Args:
        story_text: User's original travel story.
        selected_images: Top-ranked images chosen for the post.
        story_analysis: Structured metadata extracted from the story.

    Returns:
        Draft caption string ready for user review.
    """
    system_prompt = _CAPTION_PROMPT_PATH.read_text()
    client = get_openai_client()

    image_summary = "\n".join(
        f"- {img['filename']} (score {img['relevance_score']:.1f}): {img['reason']}"
        for img in selected_images
    )

    user_content = (
        f"Story:\n{story_text}\n\n"
        f"Story analysis:\n"
        f"  Location: {story_analysis['location']}\n"
        f"  Main event: {story_analysis['main_event']}\n"
        f"  Emotional tone: {story_analysis['emotional_tone']}\n"
        f"  Suggested tone: {story_analysis['suggested_facebook_tone']}\n\n"
        f"Selected photos:\n{image_summary}"
    )

    response = client.chat.completions.create(
        model=config.TEXT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=512,
    )

    caption = (response.choices[0].message.content or "").strip()
    logger.info("Caption generated (%d chars)", len(caption))
    return caption


# --- LangGraph node ---

def caption_generation_node(state: AgentState) -> AgentState:
    """LangGraph node that generates a caption draft and updates shared state."""
    analysis = state.get("story_analysis")
    if not analysis:
        err = "story_analysis missing — cannot generate caption"
        return {**state, "errors": state["errors"] + [err]}

    try:
        caption = generate_facebook_caption(
            state["story_text"], state["selected_images"], analysis
        )
        return {**state, "caption_draft": caption, "final_caption": caption}
    except Exception as exc:
        logger.error("caption_generation_node failed: %s", exc)
        return {**state, "errors": state["errors"] + [str(exc)]}
