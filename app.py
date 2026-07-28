"""Travel Social Agent — a guided five-step composer for Facebook Page posts.

Story → Photos → Recommendations → Caption → Publish

This module is the presentation layer only. All reasoning lives in
``src/agents`` and all side effects live in ``src/tools``.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Travel Social Agent",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from src.ui import components as ui  # noqa: E402
from src.ui import theme  # noqa: E402

theme.inject()

# ── Selection presets ─────────────────────────────────────────────────────────
#
# The user chooses intent ("only the best"); the numeric threshold that intent
# maps to stays internal.

SELECTIVITY = {
    "Only the best": 8.0,
    "Balanced": 6.5,
    "Include more": 5.0,
}

# ── Session state ─────────────────────────────────────────────────────────────


def _init_session() -> None:
    defaults: dict[str, Any] = {
        "story_text": "",
        "photo_folder": str(Path(__file__).parent / "data" / "photos"),
        "image_candidates": [],
        "story_analysis": None,
        "ranked_images": [],
        "selected_images": [],
        "caption_draft": "",
        "final_caption": "",
        "approval_status": "pending",
        "facebook_post_result": None,
        "errors": [],
        "dry_run": True,
        "selectivity": "Balanced",
        "max_photos": 5,
        "phase": "story",
        "draft_id": None,
        "compare_with": None,
        "page_identity": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()


def _seed_preview() -> None:
    """Development only: jump straight to Recommendations with local photos.

    Enabled with ``TSA_UI_PREVIEW=1`` or ``?preview=1``; pass ``?preview=caption``
    to land on the caption step instead. Lets the screens be opened and visually
    checked without spending API calls. Never runs otherwise.
    """
    param = st.query_params.get("preview")
    enabled = os.getenv("TSA_UI_PREVIEW") == "1" or param in ("1", "caption")
    if not enabled or st.session_state.ranked_images:
        return
    from src.tools.image_tools import scan_local_images

    reasons = [
        "Shows the courtyard and the low evening light you described.",
        "Captures the crowd gathered before the ceremony began.",
        "The architecture matches the place at the centre of your story.",
        "Same trip and mood, though the subject is less specific.",
        "A quiet detail shot that fits the reflective tone.",
        "Unrelated to this story — different place and occasion.",
    ]
    scores = [9.2, 8.4, 7.6, 6.8, 5.2, 2.4]
    candidates = scan_local_images(str(Path(__file__).parent / "data" / "photos"))
    st.session_state.image_candidates = candidates
    st.session_state.ranked_images = [
        {
            "path": c["path"],
            "filename": c["filename"],
            "relevance_score": scores[i % len(scores)],
            "reason": reasons[i % len(reasons)],
        }
        for i, c in enumerate(candidates)
    ]
    st.session_state.story_analysis = {
        "location": "Istanbul, Türkiye",
        "main_event": "Watching a whirling dervish ceremony",
        "emotional_tone": "reflective",
        "key_objects_scenes": ["dervishes", "courtyard", "evening light"],
        "suggested_facebook_tone": "warm and personal",
    }
    st.session_state.story_text = "A quiet evening in Istanbul watching a whirling dervish ceremony."
    derive_selection()

    if param == "caption":
        st.session_state.caption_draft = st.session_state.final_caption = (
            "We almost walked past the door. It looked like every other door on that "
            "street, and then someone held it open and there was a courtyard behind it, "
            "already half full, everyone waiting without really talking.\n\n"
            "I have never heard a room that quiet."
        )
        st.session_state.page_identity = {"connected": True, "name": "Iris travel blog", "id": "0"}
        st.session_state.phase = "caption"
    else:
        st.session_state.phase = "recommend"


def goto(phase: str) -> None:
    st.session_state.phase = phase
    st.rerun()


def reset_all() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ── Selection helpers (ordering lives here; scoring lives in the agent) ───────


def threshold() -> float:
    return SELECTIVITY.get(st.session_state.selectivity, 6.5)


def by_path(path: str) -> Optional[dict[str, Any]]:
    for img in st.session_state.ranked_images:
        if img["path"] == path:
            return img
    return None


def selected_paths() -> list[str]:
    return [img["path"] for img in st.session_state.selected_images]


def derive_selection() -> None:
    """Seed the ordered post from the agent's ranking. Called once, and on reset."""
    from src.tools.image_tools import select_best_images

    st.session_state.selected_images = select_best_images(
        st.session_state.ranked_images,
        max_images=st.session_state.max_photos,
        min_score=threshold(),
    )


def add_to_post(path: str) -> None:
    img = by_path(path)
    if img and path not in selected_paths():
        st.session_state.selected_images.append(img)


def remove_from_post(path: str) -> None:
    st.session_state.selected_images = [
        img for img in st.session_state.selected_images if img["path"] != path
    ]


def make_cover(path: str) -> None:
    items = st.session_state.selected_images
    for i, img in enumerate(items):
        if img["path"] == path:
            items.insert(0, items.pop(i))
            return


def move(path: str, delta: int) -> None:
    items = st.session_state.selected_images
    for i, img in enumerate(items):
        if img["path"] == path:
            j = max(0, min(len(items) - 1, i + delta))
            items[i], items[j] = items[j], items[i]
            return


def partition() -> tuple[list[dict], list[dict], list[dict]]:
    """Split every scored photo into in-post, alternatives, and poor matches."""
    chosen = selected_paths()
    alternatives, excluded = [], []
    for img in sorted(
        st.session_state.ranked_images,
        key=lambda x: x["relevance_score"],
        reverse=True,
    ):
        if img["path"] in chosen:
            continue
        if img["relevance_score"] >= ui.TIER_MAYBE:
            alternatives.append(img)
        else:
            excluded.append(img)
    return st.session_state.selected_images, alternatives, excluded


# ── Compare dialog ────────────────────────────────────────────────────────────


@st.dialog("Compare photos", width="large")
def compare_dialog(candidate: dict[str, Any]) -> None:
    """Side-by-side comparison of a candidate against the current cover."""
    current = st.session_state.selected_images[0] if st.session_state.selected_images else None

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<p class="tsa-eyebrow">Current cover</p>', unsafe_allow_html=True)
        if current:
            ui.photo_tile(current, key="cmp-current", show_tier=True)
        else:
            ui.empty_state("No cover yet", "Your post has no photos selected.")
    with right:
        st.markdown('<p class="tsa-eyebrow">Candidate</p>', unsafe_allow_html=True)
        ui.photo_tile(candidate, key="cmp-candidate", show_tier=True)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Use as cover", type="primary", use_container_width=True):
            add_to_post(candidate["path"])
            make_cover(candidate["path"])
            st.session_state.compare_with = None
            st.rerun()
    with c2:
        in_post = candidate["path"] in selected_paths()
        if st.button(
            "Already in post" if in_post else "Add to post",
            disabled=in_post,
            use_container_width=True,
        ):
            add_to_post(candidate["path"])
            st.session_state.compare_with = None
            st.rerun()
    with c3:
        if st.button("Keep current", use_container_width=True):
            st.session_state.compare_with = None
            st.rerun()


# ── Chrome ────────────────────────────────────────────────────────────────────

_seed_preview()

# Play the page-turn only when the step actually changed, never on an ordinary
# widget rerun. The counter guarantees a fresh animation name each time.
if st.session_state.get("_turn_phase") != st.session_state.phase:
    st.session_state["_turn_phase"] = st.session_state.phase
    st.session_state["_turn_n"] = st.session_state.get("_turn_n", 0) + 1
    theme.page_turn(f"{st.session_state.phase}{st.session_state['_turn_n']}")

ui.topbar()
ui.stepper(st.session_state.phase)


# ══════════════════════════════════════════════════════════════════════════════
# 1 — Story
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.phase == "story":
    st.markdown('<p class="tsa-display">What do you want to share?</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="tsa-sub">Write it the way you would tell a friend. Details about '
        "place, people, and how it felt help the most — those are what your photos "
        "get matched against.</p>",
        unsafe_allow_html=True,
    )

    story = st.text_area(
        label="story",
        label_visibility="collapsed",
        value=st.session_state.story_text,
        placeholder=(
            "Last April I wandered into a tiny coffee shop in Chengdu that had been "
            "run by the same family for three generations. The owner handed me a cup "
            "without asking what I wanted — just smiled and said I looked like a "
            "light roast person. She was right."
        ),
        height=200,
        key="story_input",
    )

    ui.rule()
    ui.section(
        "Where are your photos?",
        "Point to a folder on this computer. It can contain photos from other trips — "
        "the ones that do not fit your story will be set aside.",
    )
    folder = st.text_input(
        label="folder",
        label_visibility="collapsed",
        value=st.session_state.photo_folder,
        key="folder_input",
    )

    folder_path = Path(folder) if folder else None
    folder_ok = False
    if folder_path:
        if not folder_path.exists():
            st.markdown(
                f'<p class="tsa-meta" style="color:{theme.DANGER}">'
                f"That folder does not exist. Check the path and try again.</p>",
                unsafe_allow_html=True,
            )
        elif not folder_path.is_dir():
            st.markdown(
                f'<p class="tsa-meta" style="color:{theme.DANGER}">'
                f"That is a file, not a folder.</p>",
                unsafe_allow_html=True,
            )
        else:
            exts = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")
            count = sum(1 for f in folder_path.iterdir() if f.suffix.lower() in exts)
            folder_ok = count > 0
            tone = theme.INK_MUTED if count else theme.DANGER
            word = "photo" if count == 1 else "photos"
            msg = f"{count} {word} found" if count else "No photos found in this folder"
            st.markdown(f'<p class="tsa-meta" style="color:{tone}">{msg}</p>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
    ready = bool(story.strip()) and folder_ok
    _, act = st.columns([3, 1])
    with act:
        if st.button("Continue", type="primary", disabled=not ready, use_container_width=True):
            st.session_state.story_text = story.strip()
            st.session_state.photo_folder = str(folder_path)
            st.session_state.image_candidates = []
            goto("photos")


# ══════════════════════════════════════════════════════════════════════════════
# 2 — Photos
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.phase == "photos":
    from src.tools.image_tools import scan_local_images

    if not st.session_state.image_candidates:
        with st.spinner("Reading your folder…"):
            try:
                st.session_state.image_candidates = scan_local_images(st.session_state.photo_folder)
                st.session_state.errors = []
            except Exception as exc:
                logger.error("Scan failed: %s", exc)
                st.session_state.errors = [str(exc)]

    candidates = st.session_state.image_candidates

    if st.session_state.errors:
        ui.empty_state("Could not read that folder", st.session_state.errors[0])
    elif not candidates:
        ui.empty_state(
            "No photos here",
            "This folder has no JPG, PNG, WebP, or HEIC files. Go back and choose another.",
        )
    else:
        n = len(candidates)
        st.markdown(
            f'<p class="tsa-display">{n} {"photo" if n == 1 else "photos"} ready</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="tsa-sub">Next, each one is looked at and matched against your '
            "story. Photos that do not belong will be set aside — you can always bring "
            "them back.</p>",
            unsafe_allow_html=True,
        )
        ui.contact_sheet(candidates, columns=4, key="scan")

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    back, _, fwd = st.columns([1, 2, 1.4])
    with back:
        if st.button("Back", use_container_width=True):
            st.session_state.image_candidates = []
            goto("story")
    with fwd:
        has_key = bool(os.getenv("OPENAI_API_KEY"))
        if st.button(
            "Find the best photos",
            type="primary",
            disabled=not (candidates and has_key),
            use_container_width=True,
        ):
            st.session_state.ranked_images = []
            st.session_state.selected_images = []
            st.session_state.story_analysis = None
            goto("recommend")
        if not has_key:
            st.markdown(
                f'<p class="tsa-meta" style="color:{theme.DANGER}">OPENAI_API_KEY is not set.</p>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# 3 — Recommendations   ◀ the screen this redesign centres on
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.phase == "recommend":
    from src.agents.photo_ranker import score_image_relevance
    from src.agents.story_analyzer import analyze_story

    # ── Run the pipeline once, with honest per-photo progress ────────────────
    if not st.session_state.ranked_images:
        candidates = st.session_state.image_candidates
        total = len(candidates)
        try:
            with st.status("Reading your story…", expanded=False) as status:
                analysis = analyze_story(st.session_state.story_text)
                st.session_state.story_analysis = analysis

                ranked: list[dict[str, Any]] = []
                for i, cand in enumerate(candidates, start=1):
                    status.update(label=f"Looking at photo {i} of {total}…")
                    try:
                        ranked.append(
                            score_image_relevance(cand["path"], dict(analysis), st.session_state.story_text)
                        )
                    except Exception as exc:
                        logger.warning("Could not score %s: %s", cand["filename"], exc)

                st.session_state.ranked_images = ranked
                derive_selection()
                status.update(label="Done", state="complete")
        except Exception as exc:
            logger.error("Recommendation pipeline failed: %s", exc)
            ui.empty_state("Something went wrong", str(exc))
            if st.button("Try again", type="primary"):
                st.session_state.ranked_images = []
                st.rerun()
            st.stop()

    in_post, alternatives, excluded = partition()

    if st.session_state.compare_with:
        candidate = by_path(st.session_state.compare_with)
        if candidate:
            compare_dialog(candidate)

    # ── Header + selection controls ──────────────────────────────────────────
    head, ctrl = st.columns([3, 1.1])
    with head:
        st.markdown('<p class="tsa-display">Your photo picks</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="tsa-sub">{len(in_post)} of {len(st.session_state.ranked_images)} photos '
            "chosen for this post, in the order they will appear. Change anything you like.</p>",
            unsafe_allow_html=True,
        )
    with ctrl:
        with st.popover("Adjust", use_container_width=True):
            st.markdown('<p class="tsa-eyebrow">How selective?</p>', unsafe_allow_html=True)
            choice = st.segmented_control(
                "selectivity",
                options=list(SELECTIVITY.keys()),
                default=st.session_state.selectivity,
                label_visibility="collapsed",
            )
            if choice:
                st.session_state.selectivity = choice
            st.session_state.max_photos = st.slider(
                "Most photos to include", 1, 10, st.session_state.max_photos
            )
            if st.button("Reset to suggested", use_container_width=True):
                derive_selection()
                st.rerun()

    # ── Cover ────────────────────────────────────────────────────────────────
    if in_post:
        cover = in_post[0]
        cov_img, cov_meta = st.columns([1.45, 1], gap="medium")
        with cov_img:
            ui.cover_photo(cover, key="lead")
        with cov_meta:
            st.markdown('<span class="tsa-pill tsa-pill--cover">Cover photo</span>', unsafe_allow_html=True)
            label, css = ui.match_tier(cover["relevance_score"])
            st.markdown(
                f'<div style="margin-top:.5rem"><span class="tsa-pill {css}">{label}</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<p class="tsa-why tsa-why--cover">{ui.humanize_reason(cover.get("reason", ""))}</p>',
                unsafe_allow_html=True,
            )
            a, b = st.columns(2)
            with a:
                if st.button("Remove", key="cover-remove", use_container_width=True):
                    remove_from_post(cover["path"])
                    st.rerun()
            with b:
                if st.button(
                    "Compare",
                    key="cover-compare",
                    use_container_width=True,
                    disabled=not alternatives,
                ):
                    st.session_state.compare_with = alternatives[0]["path"]
                    st.rerun()
    else:
        ui.empty_state(
            "No photos in this post yet",
            "Nothing cleared the bar you set. Loosen it under Adjust, or add photos "
            "from the suggestions below.",
        )

    # ── Supporting photos ────────────────────────────────────────────────────
    rest = in_post[1:]
    if rest:
        st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        ui.section("Also in this post", "Shown in order after the cover.")
        cols = st.columns(min(len(rest), 4), gap="small")
        for i, (col, img) in enumerate(zip(cols, rest)):
            position = i + 2
            with col:

                def _actions(p: str = img["path"], idx: int = i + 1, last: int = len(in_post) - 1) -> None:
                    # Trailing spacer keeps the controls clustered left rather than
                    # stretched across the tile.
                    c1, c2, c3, c4, _sp = st.columns([1, 1, 1, 1, 1.5])
                    if c1.button("★", key=f"cov-{p}", help="Make cover"):
                        make_cover(p)
                        st.rerun()
                    if c2.button("◀", key=f"up-{p}", help="Move earlier", disabled=idx <= 1):
                        move(p, -1)
                        st.rerun()
                    if c3.button("▶", key=f"dn-{p}", help="Move later", disabled=idx >= last):
                        move(p, 1)
                        st.rerun()
                    if c4.button("✕", key=f"rm-{p}", help="Remove"):
                        remove_from_post(p)
                        st.rerun()

                ui.photo_tile(img, key=f"sel-{i}", order=position, actions=_actions)

    # ── Alternatives ─────────────────────────────────────────────────────────
    if alternatives:
        ui.rule()
        ui.section(
            "Other photos that could work",
            "These fit your story too, just less closely. Swap any of them in.",
        )
        cols = st.columns(4, gap="small")
        for i, img in enumerate(alternatives[:8]):
            with cols[i % 4]:

                def _alt_actions(p: str = img["path"]) -> None:
                    c1, c2 = st.columns(2)
                    if c1.button("Add", key=f"add-{p}", use_container_width=True):
                        add_to_post(p)
                        st.rerun()
                    if c2.button("Compare", key=f"cmp-{p}", use_container_width=True):
                        st.session_state.compare_with = p
                        st.rerun()

                ui.photo_tile(img, key=f"alt-{i}", actions=_alt_actions)

    # ── Set aside ────────────────────────────────────────────────────────────
    if excluded:
        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
        n_ex = len(excluded)
        with st.expander(
            f"Set aside — {n_ex} {'photo that does' if n_ex == 1 else 'photos that do'} not fit this story"
        ):
            cols = st.columns(4, gap="small")
            for i, img in enumerate(excluded):
                with cols[i % 4]:

                    def _ex_actions(p: str = img["path"]) -> None:
                        if st.button("Add anyway", key=f"exadd-{p}", use_container_width=True):
                            add_to_post(p)
                            st.rerun()

                    ui.photo_tile(img, key=f"ex-{i}", dimmed=True, actions=_ex_actions)

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    back, _, fwd = st.columns([1, 2, 1.4])
    with back:
        if st.button("Back", use_container_width=True):
            goto("photos")
    with fwd:
        if st.button(
            "Write the caption",
            type="primary",
            disabled=not in_post,
            use_container_width=True,
        ):
            st.session_state.caption_draft = ""
            st.session_state.final_caption = ""
            goto("caption")


# ══════════════════════════════════════════════════════════════════════════════
# 4 — Caption
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.phase == "caption":
    from src.agents.caption_writer import generate_facebook_caption
    from src.tools.database_tool import init_db, save_draft_to_db

    if not st.session_state.caption_draft:
        with st.spinner("Writing a first draft…"):
            try:
                caption = generate_facebook_caption(
                    st.session_state.story_text,
                    st.session_state.selected_images,
                    st.session_state.story_analysis,
                )
                st.session_state.caption_draft = caption
                st.session_state.final_caption = caption
            except Exception as exc:
                logger.error("Caption generation failed: %s", exc)
                ui.empty_state("Could not write a caption", str(exc))
                if st.button("Try again", type="primary"):
                    st.rerun()
                st.stop()

    st.markdown('<p class="tsa-display">Your caption</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="tsa-sub">Edit it directly, or ask for a revision. '
        "Your edits are always the starting point for a revision.</p>",
        unsafe_allow_html=True,
    )

    edit_col, prev_col = st.columns([1.15, 1], gap="large")

    with edit_col:
        edited = st.text_area(
            label="caption",
            label_visibility="collapsed",
            value=st.session_state.final_caption,
            height=230,
            key="caption_editor",
        )
        st.session_state.final_caption = edited
        st.markdown(
            f'<p class="tsa-meta">{len(edited)} characters</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<p class="tsa-eyebrow" style="margin-top:1rem">Revise</p>', unsafe_allow_html=True)
        revisions = {
            "Make shorter": "Rewrite it shorter — at most three sentences. Keep the specific details.",
            "More personal": "Rewrite it in a more personal, first-person voice. Less description, more feeling.",
            "Focus on the people": "Rewrite it centred on the people in the story rather than the place.",
            "Try another opening": "Rewrite it with a completely different opening line. Keep the rest of the meaning.",
        }
        r1, r2 = st.columns(2)
        for i, (label, instruction) in enumerate(revisions.items()):
            target = r1 if i % 2 == 0 else r2
            with target:
                if st.button(label, key=f"rev-{i}", use_container_width=True):
                    with st.spinner("Revising…"):
                        try:
                            revised = generate_facebook_caption(
                                f"{st.session_state.story_text}\n\n"
                                f"Current caption:\n{st.session_state.final_caption}\n\n"
                                f"Revision request: {instruction}",
                                st.session_state.selected_images,
                                st.session_state.story_analysis,
                            )
                            st.session_state.final_caption = revised
                            st.session_state.caption_draft = revised
                            st.rerun()
                        except Exception as exc:
                            st.markdown(
                                f'<p class="tsa-meta" style="color:{theme.DANGER}">'
                                f"Revision failed: {exc}</p>",
                                unsafe_allow_html=True,
                            )

        if st.button("Save as draft", use_container_width=True):
            try:
                init_db()
                st.session_state.draft_id = save_draft_to_db(
                    story_text=st.session_state.story_text,
                    caption_draft=st.session_state.final_caption,
                    selected_image_paths=selected_paths(),
                    story_analysis=dict(st.session_state.story_analysis or {}),
                    status="draft",
                )
                st.markdown(
                    f'<p class="tsa-meta" style="color:{theme.POSITIVE}">'
                    f"Saved as draft #{st.session_state.draft_id}.</p>",
                    unsafe_allow_html=True,
                )
            except Exception as exc:
                st.markdown(
                    f'<p class="tsa-meta" style="color:{theme.DANGER}">Could not save: {exc}</p>',
                    unsafe_allow_html=True,
                )

    with prev_col:
        st.markdown('<p class="tsa-eyebrow">Preview</p>', unsafe_allow_html=True)
        if st.session_state.page_identity is None:
            from src.tools.facebook_tool import get_page_identity

            st.session_state.page_identity = get_page_identity()
        page = st.session_state.page_identity
        ui.facebook_preview(page["name"], st.session_state.final_caption, st.session_state.selected_images)

    st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
    back, _, fwd = st.columns([1, 2, 1.4])
    with back:
        if st.button("Back", use_container_width=True):
            goto("recommend")
    with fwd:
        if st.button(
            "Review and publish",
            type="primary",
            disabled=not st.session_state.final_caption.strip(),
            use_container_width=True,
        ):
            goto("publish")


# ══════════════════════════════════════════════════════════════════════════════
# 5 — Review and publish
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.phase == "publish":
    from src.tools.database_tool import init_db, save_draft_to_db, update_draft_status
    from src.tools.facebook_tool import get_page_identity, post_to_facebook_page

    if st.session_state.page_identity is None:
        st.session_state.page_identity = get_page_identity()
    page = st.session_state.page_identity
    photos = st.session_state.selected_images

    st.markdown('<p class="tsa-display">Ready to publish</p>', unsafe_allow_html=True)

    if page["connected"]:
        st.markdown(
            f'<p class="tsa-sub">This will be published to '
            f'<strong style="color:{theme.INK}">{page["name"]}</strong>. '
            f"Nothing has been posted yet.</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<p class="tsa-sub" style="color:{theme.DANGER}">'
            f"Not connected to a Facebook Page — {page.get('error', 'check your credentials')}. "
            f"You can still preview and save, but publishing is unavailable.</p>",
            unsafe_allow_html=True,
        )

    ui.facebook_preview(page["name"], st.session_state.final_caption, photos)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    mode_col, act_col = st.columns([1.3, 1])
    with mode_col:
        st.session_state.dry_run = st.toggle(
            "Practice run — do not actually publish",
            value=st.session_state.dry_run,
        )
        n = len(photos)
        detail = f"{n} {'photo' if n == 1 else 'photos'} · {len(st.session_state.final_caption)} characters"
        st.markdown(f'<p class="tsa-meta">{detail}</p>', unsafe_allow_html=True)

    with act_col:
        can_publish = page["connected"] or st.session_state.dry_run
        label = "Do a practice run" if st.session_state.dry_run else "Publish to Facebook"
        if st.button(label, type="primary", disabled=not can_publish, use_container_width=True):
            st.session_state.approval_status = "approved"
            with st.spinner("Publishing…"):
                result = post_to_facebook_page(
                    message=st.session_state.final_caption,
                    image_paths=[img["path"] for img in photos],
                    dry_run=st.session_state.dry_run,
                )
            st.session_state.facebook_post_result = result
            try:
                init_db()
                status = "posted" if result.get("success") else "failed"
                if st.session_state.draft_id:
                    update_draft_status(st.session_state.draft_id, status=status, post_result=result)
                else:
                    st.session_state.draft_id = save_draft_to_db(
                        story_text=st.session_state.story_text,
                        caption_draft=st.session_state.final_caption,
                        selected_image_paths=[img["path"] for img in photos],
                        story_analysis=dict(st.session_state.story_analysis or {}),
                        status=status,
                    )
            except Exception as exc:
                logger.warning("Draft persistence failed: %s", exc)
            goto("done")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    back, _ = st.columns([1, 3])
    with back:
        if st.button("Back", use_container_width=True):
            goto("caption")


# ══════════════════════════════════════════════════════════════════════════════
# Done
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.phase == "done":
    result = st.session_state.facebook_post_result or {}
    page = st.session_state.page_identity or {"name": "your Page"}

    if result.get("success") and result.get("dry_run"):
        st.markdown('<p class="tsa-display">Practice run finished</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="tsa-sub">Nothing was published. Everything worked — turn off '
            "the practice toggle to post for real.</p>",
            unsafe_allow_html=True,
        )
        ui.facebook_preview(page["name"], st.session_state.final_caption, st.session_state.selected_images)
        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
        a, b, _ = st.columns([1.3, 1.3, 1])
        with a:
            if st.button("Publish for real", type="primary", use_container_width=True):
                st.session_state.dry_run = False
                goto("publish")
        with b:
            if st.button("Start a new post", use_container_width=True):
                reset_all()

    elif result.get("success"):
        st.markdown('<p class="tsa-display">Published</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="tsa-sub">Your post is live on '
            f'<strong style="color:{theme.INK}">{page["name"]}</strong>.</p>',
            unsafe_allow_html=True,
        )
        ui.facebook_preview(page["name"], st.session_state.final_caption, st.session_state.selected_images)
        st.markdown(
            f'<p class="tsa-meta" style="margin-top:1rem">Post ID {result.get("post_id")}</p>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        a, _ = st.columns([1.3, 2])
        with a:
            if st.button("Start a new post", type="primary", use_container_width=True):
                reset_all()

    else:
        err = result.get("error", {})
        message = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        is_permission = "permission" in message.lower() or "does not exist" in message.lower()

        st.markdown('<p class="tsa-display">Could not publish</p>', unsafe_allow_html=True)
        if is_permission:
            st.markdown(
                '<p class="tsa-sub">Facebook refused the request. This usually means the '
                "Page access token has expired or is missing permission to post. Your "
                "caption and photos are saved — reconnect and try again.</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p class="tsa-sub">Facebook rejected the post. Your caption and photos '
                "are saved.</p>",
                unsafe_allow_html=True,
            )
        ui.empty_state("What Facebook said", message)

        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
        a, b, _ = st.columns([1.2, 1.2, 1])
        with a:
            if st.button("Try again", type="primary", use_container_width=True):
                st.session_state.facebook_post_result = None
                goto("publish")
        with b:
            if st.button("Start over", use_container_width=True):
                reset_all()
