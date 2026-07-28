"""LangGraph workflow definition for the Travel Social Agent."""

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from src.agents.caption_writer import caption_generation_node
from src.agents.photo_ranker import (
    photo_relevance_node,
    photo_scan_node,
    photo_selection_node,
)
from src.agents.story_analyzer import story_analysis_node
from src.state import AgentState
from src.tools.database_tool import save_draft_to_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Human-in-the-loop and posting nodes (Milestones 3–5)
# ---------------------------------------------------------------------------

def human_review_node(state: AgentState) -> AgentState:
    """Pause point for human review. The Streamlit UI handles approval externally.

    In a headless pipeline this node would block on user input.
    When used via Streamlit, approval_status is set by the UI before
    the graph continues.
    """
    # State flows through unchanged; approval happens outside the graph.
    return state


def facebook_post_node(state: AgentState) -> AgentState:
    """Post to Facebook if approved. (Milestone 4)"""
    from src.tools.facebook_tool import post_to_facebook_page

    if state.get("approval_status") != "approved":
        logger.info("Post not approved — skipping Facebook posting.")
        return state

    caption = state.get("final_caption") or state.get("caption_draft", "")
    image_paths = [img["path"] for img in state.get("selected_images", [])]

    result = post_to_facebook_page(
        message=caption,
        image_paths=image_paths,
        dry_run=state.get("dry_run", True),
    )

    # Persist result
    try:
        save_draft_to_db(
            story_text=state["story_text"],
            caption_draft=caption,
            selected_image_paths=image_paths,
            story_analysis=dict(state.get("story_analysis") or {}),
            status="posted" if result.get("success") else "failed",
        )
    except Exception as exc:
        logger.warning("Could not save to DB: %s", exc)

    return {**state, "facebook_post_result": result}


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

def _route_after_scan(state: AgentState) -> Literal["story_analysis", "end"]:
    if state["errors"] or not state["image_candidates"]:
        return "end"
    return "story_analysis"


def _route_after_review(state: AgentState) -> Literal["facebook_post", "end"]:
    if state.get("approval_status") == "approved":
        return "facebook_post"
    return "end"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and compile the agent workflow graph."""
    builder = StateGraph(AgentState)

    # Nodes
    builder.add_node("photo_scan", photo_scan_node)
    builder.add_node("story_analysis", story_analysis_node)
    builder.add_node("photo_relevance", photo_relevance_node)
    builder.add_node("photo_selection", photo_selection_node)
    builder.add_node("caption_generation", caption_generation_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("facebook_post", facebook_post_node)

    # Edges — linear pipeline with a conditional branch after scan
    builder.add_edge(START, "photo_scan")
    builder.add_conditional_edges("photo_scan", _route_after_scan)
    builder.add_edge("story_analysis", "photo_relevance")
    builder.add_edge("photo_relevance", "photo_selection")
    builder.add_edge("photo_selection", "caption_generation")
    builder.add_edge("caption_generation", "human_review")
    builder.add_conditional_edges("human_review", _route_after_review)
    builder.add_edge("facebook_post", END)

    return builder.compile()


# Module-level compiled graph (lazy import safe)
graph = build_graph()
