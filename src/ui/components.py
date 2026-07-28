"""Reusable presentation components.

This module owns *presentation only*. It never calls the OpenAI or Meta APIs and
never mutates agent state — it renders what the agent layer produced and returns
user intent back to the caller.
"""

import html
import re
from pathlib import Path
from typing import Any, Callable, Optional

import streamlit as st
from PIL import Image

# ── Match tiers ───────────────────────────────────────────────────────────────
#
# The vision model returns a 1–10 score. That number is an implementation
# detail: it is never rendered. It is translated into language a person can act
# on, and only ever used for ordering and tiering.

TIER_STRONG = 8.0
TIER_GOOD = 6.5
TIER_MAYBE = 4.5

_TIER_LABELS = [
    (TIER_STRONG, "Strong match", "tsa-pill--strong"),
    (TIER_GOOD, "Good match", "tsa-pill--good"),
    (TIER_MAYBE, "Possible", "tsa-pill--maybe"),
]


def match_tier(score: float) -> tuple[str, str]:
    """Translate a relevance score into a human label and its pill class.

    Args:
        score: Raw 1–10 relevance score from the vision model.

    Returns:
        Tuple of (label, css_class).
    """
    for threshold, label, css in _TIER_LABELS:
        if score >= threshold:
            return label, css
    return "Not a match", "tsa-pill"


_SCORE_NOISE = re.compile(r"^\s*(score\s*[:\-]?\s*[0-9.]+\s*[,.;\-]?\s*)?(reason\s*[:\-]\s*)?", re.I)


def humanize_reason(reason: str) -> str:
    """Strip model-format artefacts from a reason string and tidy it for display.

    Args:
        reason: Raw reason text returned by the scoring prompt.

    Returns:
        A clean sentence safe to render, or a neutral fallback.
    """
    if not reason:
        return "Fits the mood of your story."
    cleaned = _SCORE_NOISE.sub("", reason.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .;,")
    if not cleaned:
        return "Fits the mood of your story."
    cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned + "."


# ── Chrome ────────────────────────────────────────────────────────────────────

STEPS = ["Story", "Photos", "Recommendations", "Caption", "Publish"]
PHASE_INDEX = {
    "story": 0,
    "photos": 1,
    "recommend": 2,
    "caption": 3,
    "publish": 4,
    "done": 5,
}


def topbar(right_slot: str = "") -> None:
    """Render the minimal application top bar."""
    st.markdown(
        f'<div class="tsa-topbar">'
        f'<div class="tsa-wordmark">Travel Social Agent</div>'
        f'<div class="tsa-meta">{right_slot}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def stepper(phase: str) -> None:
    """Render the five-step progress indicator."""
    current = PHASE_INDEX.get(phase, 0)
    parts: list[str] = []
    for i, label in enumerate(STEPS):
        if i < current:
            state, mark = "is-done", "✓"
        elif i == current:
            state, mark = "is-current", str(i + 1)
        else:
            state, mark = "", str(i + 1)
        parts.append(
            f'<div class="tsa-step {state}">'
            f'<span class="tsa-step-dot">{mark}</span>'
            f'<span class="tsa-step-label">{label}</span>'
            f"</div>"
        )
        if i < len(STEPS) - 1:
            parts.append('<div class="tsa-step-rule"></div>')
    st.markdown(f'<div class="tsa-steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def section(title: str, sub: str = "", eyebrow: str = "") -> None:
    """Render a section heading with optional eyebrow and supporting line."""
    out = ""
    if eyebrow:
        out += f'<p class="tsa-eyebrow">{html.escape(eyebrow)}</p>'
    out += f'<p class="tsa-title">{html.escape(title)}</p>'
    if sub:
        out += f'<p class="tsa-sub">{html.escape(sub)}</p>'
    st.markdown(out, unsafe_allow_html=True)


def rule() -> None:
    st.markdown('<hr class="tsa-rule">', unsafe_allow_html=True)


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f'<div class="tsa-empty">'
        f'<div class="tsa-empty-title">{html.escape(title)}</div>'
        f'<div class="tsa-empty-body">{html.escape(body)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


# ── Photo rendering ───────────────────────────────────────────────────────────


def _open(path: str) -> Optional[Image.Image]:
    try:
        return Image.open(path)
    except Exception:
        return None


def cover_photo(img: dict[str, Any], key: str = "cover") -> None:
    """Render the hero cover photo with its reason."""
    with st.container(key=f"tsacover-{key}"):
        image = _open(img["path"])
        if image is not None:
            st.image(image, width="stretch")
        else:
            empty_state("Photo unavailable", "This file could not be opened.")


def photo_tile(
    img: dict[str, Any],
    key: str,
    order: Optional[int] = None,
    show_tier: bool = True,
    dimmed: bool = False,
    show_reason: bool = True,
    actions: Optional[Callable[[], None]] = None,
) -> None:
    """Render a single photo tile with its badge, reason, and action row.

    Args:
        img: A ranked-image dict (path, filename, relevance_score, reason).
        key: Unique DOM/scope key for this tile.
        order: 1-based position badge, if the photo is in the post.
        show_tier: Whether to show the match-quality pill.
        dimmed: Render de-emphasised (used for excluded photos).
        show_reason: Whether to render the reason line.
        actions: Optional callable rendering controls inside the tile surface.
    """
    scope = f"tsatile-{key}" + ("-tsadim" if dimmed else "")
    with st.container(key=scope):
        image = _open(img["path"])
        if image is not None:
            st.image(image, width="stretch")

        badges = ""
        if order is not None:
            badges += f'<span class="tsa-pill tsa-pill--order">{order}</span> '
        if show_tier:
            label, css = match_tier(float(img.get("relevance_score", 0)))
            badges += f'<span class="tsa-pill {css}">{label}</span>'
        if badges:
            st.markdown(f'<div style="margin-top:.45rem">{badges}</div>', unsafe_allow_html=True)

        if show_reason:
            st.markdown(
                f'<p class="tsa-why">{html.escape(humanize_reason(img.get("reason", "")))}</p>',
                unsafe_allow_html=True,
            )

        if actions is not None:
            actions()


def contact_sheet(images: list[dict[str, Any]], columns: int = 4, key: str = "sheet") -> None:
    """Render a plain contact sheet of photos with no metadata chrome."""
    for row_start in range(0, len(images), columns):
        row = images[row_start : row_start + columns]
        cols = st.columns(columns, gap="small")
        for offset, (col, img) in enumerate(zip(cols, row)):
            with col:
                with st.container(key=f"tsatile-{key}-{row_start + offset}"):
                    image = _open(img["path"])
                    if image is not None:
                        st.image(image, width="stretch")


# ── Facebook preview ──────────────────────────────────────────────────────────


def facebook_preview(page_name: str, caption: str, photos: list[dict[str, Any]]) -> None:
    """Render a faithful Facebook Page post preview.

    Args:
        page_name: Display name of the connected Page.
        caption: Post body text.
        photos: Ordered photos; the first is the lead image.
    """
    initial = (page_name or "P").strip()[:1].upper()

    # st.markdown parses this string as Markdown before honouring the HTML, and a
    # blank line inside the block would be treated as a paragraph break — which
    # silently drops the caption's own paragraph spacing. Escaping first and then
    # emitting explicit <br> keeps the preview faithful to what will be posted.
    body = html.escape(caption).replace("\n", "<br>")

    st.markdown(
        f'<div class="tsa-fb">'
        f'<div class="tsa-fb-head">'
        f'<div class="tsa-fb-avatar">{html.escape(initial)}</div>'
        f"<div>"
        f'<div class="tsa-fb-name">{html.escape(page_name)}</div>'
        f'<div class="tsa-fb-time">Just now · 🌐 Public</div>'
        f"</div></div>"
        f'<div class="tsa-fb-body">{body}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    if not photos:
        return

    lead, rest = photos[0], photos[1:]
    with st.container(key="tsatile-fblead"):
        image = _open(lead["path"])
        if image is not None:
            st.image(image, width="stretch")

    if rest:
        cols = st.columns(min(len(rest), 4), gap="small")
        for i, (col, img) in enumerate(zip(cols, rest)):
            with col:
                with st.container(key=f"tsatile-fb-{i}"):
                    image = _open(img["path"])
                    if image is not None:
                        st.image(image, width="stretch")
