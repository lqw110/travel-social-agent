"""Agent node: analyse the user's story to extract structured metadata."""

import json
import logging
from pathlib import Path

from src.config import config
from src.services.openai_client import get_openai_client
from src.state import AgentState, StoryAnalysis

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "story_analysis_prompt.md"


def analyze_story(story_text: str) -> StoryAnalysis:
    """Extract structured metadata from a travel story using the LLM.

    Args:
        story_text: The raw story written by the user.

    Returns:
        StoryAnalysis with location, main_event, emotional_tone, etc.
    """
    system_prompt = _PROMPT_PATH.read_text()
    client = get_openai_client()

    response = client.chat.completions.create(
        model=config.TEXT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": story_text},
        ],
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    logger.info("Story analysis complete: %s", data)
    return StoryAnalysis(
        location=data.get("location", "Unknown"),
        main_event=data.get("main_event", ""),
        emotional_tone=data.get("emotional_tone", ""),
        key_objects_scenes=data.get("key_objects_scenes", []),
        suggested_facebook_tone=data.get("suggested_facebook_tone", "warm and personal"),
    )


# --- LangGraph node ---

def story_analysis_node(state: AgentState) -> AgentState:
    """LangGraph node that analyses the story and updates shared state."""
    try:
        analysis = analyze_story(state["story_text"])
        return {**state, "story_analysis": analysis}
    except Exception as exc:
        logger.error("story_analysis_node failed: %s", exc)
        return {**state, "errors": state["errors"] + [str(exc)]}
