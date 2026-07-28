"""Tool for persisting drafts and post history to SQLite."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "db" / "travel_agent.db"
SCHEMA_PATH = Path(__file__).parent.parent / "db" / "schema.sql"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _get_connection() as conn:
        schema = SCHEMA_PATH.read_text()
        conn.executescript(schema)
    logger.info("Database initialised at %s", DB_PATH)


def save_draft_to_db(
    story_text: str,
    caption_draft: str,
    selected_image_paths: list[str],
    story_analysis: Optional[dict[str, Any]] = None,
    status: str = "draft",
) -> int:
    """Save a caption draft and selected images to the database.

    Args:
        story_text: The original story entered by the user.
        caption_draft: The generated (or edited) Facebook caption.
        selected_image_paths: Paths of the images chosen for this post.
        story_analysis: Structured analysis dict from the story analyzer.
        status: Lifecycle status — 'draft', 'approved', 'posted', 'cancelled'.

    Returns:
        The row ID of the inserted draft record.
    """
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO drafts
                (story_text, caption_draft, selected_images, story_analysis, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                story_text,
                caption_draft,
                json.dumps(selected_image_paths),
                json.dumps(story_analysis) if story_analysis else None,
                status,
                datetime.utcnow().isoformat(),
            ),
        )
        row_id: int = cursor.lastrowid  # type: ignore[assignment]
    logger.info("Draft saved with id=%d, status=%s", row_id, status)
    return row_id


def update_draft_status(draft_id: int, status: str, post_result: Optional[dict] = None) -> None:
    """Update the lifecycle status of a saved draft.

    Args:
        draft_id: Primary key of the draft row.
        status: New status string.
        post_result: Optional dict from the Facebook posting tool to persist.
    """
    with _get_connection() as conn:
        conn.execute(
            """
            UPDATE drafts
            SET status = ?,
                post_result = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                json.dumps(post_result) if post_result else None,
                datetime.utcnow().isoformat(),
                draft_id,
            ),
        )
    logger.info("Draft %d updated to status=%s", draft_id, status)


def list_drafts(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recent drafts ordered by creation time."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM drafts ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
