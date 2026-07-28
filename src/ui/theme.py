"""Design tokens and global stylesheet for the Travel Social Agent UI.

The metaphor is a travel journal open on a desk: a warm textured desk surface,
a cream page sitting on it, photos taped in as prints, and handwritten accents.

Two deliberate exceptions stay clean and un-journaled:

* the Facebook preview, which must look like the real post, not like stationery;
* body copy and photo reasons, which stay in a legible sans face.
"""

import streamlit as st

# ── Tokens ────────────────────────────────────────────────────────────────────

DESK = "#D9CBB6"          # warm desk beneath the journal
DESK_DEEP = "#C9B99F"
PAGE = "#FCF9F2"          # journal paper
PAGE_EDGE = "#F0E9DA"
SURFACE = "#FFFFFF"
SURFACE_SUNK = "#F4EFE4"
INK = "#2A2520"
INK_MUTED = "#6E6558"
INK_FAINT = "#9A9084"
BORDER = "#E4DAC8"
BORDER_STRONG = "#CFC2AB"
ACCENT = "#2563EB"
POSITIVE = "#1F7A54"
CAUTION = "#8A6D1F"
DANGER = "#B4321F"
TAPE = "rgba(226, 208, 160, 0.75)"

# Retained for callers that referenced the previous palette names.
CANVAS = PAGE

RADIUS_CONTROL = "10px"
RADIUS_TILE = "6px"
RADIUS_SURFACE = "14px"

FONT_STACK = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
    '"Helvetica Neue", Arial, sans-serif'
)
HAND_STACK = '"Caveat", "Bradley Hand", "Segoe Script", cursive'

# Inline paper grain. Kept as a data URI so the page makes no network request
# for texture and still renders offline.
_GRAIN = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' "
    "height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' "
    "baseFrequency='0.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='140' "
    "height='140' filter='url(%23n)' opacity='0.35'/%3E%3C/svg%3E\")"
)


_STYLES = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&display=swap');

/* ══ Desk ══════════════════════════════════════════════════════════════════ */

html, body, [class*="css"], .stMarkdown, button, input, textarea, select {{
    font-family: {FONT_STACK};
    -webkit-font-smoothing: antialiased;
}}

.stApp {{
    background-color: {DESK};
    background-image:
        {_GRAIN},
        radial-gradient(120% 90% at 50% 0%, rgba(255,255,255,0.28), transparent 60%),
        linear-gradient(160deg, {DESK} 0%, {DESK_DEEP} 100%);
    background-blend-mode: soft-light, normal, normal;
}}

#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}

/* ══ The page ══════════════════════════════════════════════════════════════ */

[data-testid="stMain"] .block-container {{
    position: relative;
    max-width: 1080px;
    margin-top: 1.75rem;
    margin-bottom: 3rem;
    padding: 2.75rem 3rem 3.5rem 3.5rem;
    background-color: {PAGE};
    background-image:
        {_GRAIN},
        repeating-linear-gradient(
            to bottom,
            transparent 0 31px,
            rgba(120, 104, 78, 0.055) 31px 32px
        );
    background-blend-mode: soft-light, normal;
    border-radius: 3px 14px 14px 3px;
    box-shadow:
        0 1px 2px rgba(60, 46, 26, 0.10),
        0 18px 40px -18px rgba(60, 46, 26, 0.38),
        inset 0 0 0 1px rgba(255, 255, 255, 0.55);
}}

/* Bound spine and its stitching */
[data-testid="stMain"] .block-container::before {{
    content: "";
    position: absolute;
    top: 0; bottom: 0; left: 0;
    width: 26px;
    border-radius: 3px 0 0 3px;
    background: linear-gradient(90deg,
        rgba(120, 96, 60, 0.20) 0%,
        rgba(120, 96, 60, 0.07) 45%,
        transparent 100%);
    pointer-events: none;
}}
[data-testid="stMain"] .block-container::after {{
    content: "";
    position: absolute;
    top: 2.2rem; bottom: 2.2rem; left: 34px;
    width: 1px;
    background: repeating-linear-gradient(
        to bottom,
        rgba(150, 120, 80, 0.32) 0 7px,
        transparent 7px 15px
    );
    pointer-events: none;
}}

/* ══ Typography ═══════════════════════════════════════════════════════════ */
/* Streamlit ships its own `.stMarkdown p` rule at equal specificity and later in
   the cascade, so it wins ties against a bare class. These headings are emitted
   as <p> inside st.markdown and must therefore assert their own size. */

.tsa-display {{
    font-family: {HAND_STACK} !important;
    font-size: 3.5rem !important;
    line-height: 1.0 !important;
    font-weight: 700 !important;
    color: {INK};
    margin: 0 0 0.35rem 0 !important;
    transform: rotate(-0.5deg);
}}

.tsa-title {{
    font-family: {HAND_STACK} !important;
    font-size: 2.35rem !important;
    line-height: 1.1 !important;
    font-weight: 700 !important;
    color: {INK};
    margin: 0 0 0.2rem 0 !important;
    transform: rotate(-0.35deg);
}}

.tsa-sub {{
    font-size: 0.9375rem !important;
    line-height: 1.6 !important;
    color: {INK_MUTED};
    margin: 0 0 1.5rem 0 !important;
    max-width: 62ch;
}}

.tsa-meta {{
    font-size: 0.8125rem !important;
    line-height: 1.45 !important;
    color: {INK_MUTED};
}}

.tsa-eyebrow {{
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {INK_FAINT};
    margin: 0 0 0.5rem 0 !important;
}}

/* ══ Top bar ═══════════════════════════════════════════════════════════════ */

.tsa-topbar {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding-bottom: 1rem;
    margin-bottom: 1.4rem;
    border-bottom: 1px solid rgba(150, 120, 80, 0.22);
}}
.tsa-wordmark {{
    font-family: {HAND_STACK};
    font-size: 1.95rem;
    font-weight: 700;
    color: {INK};
    transform: rotate(-0.6deg);
}}

/* ══ Stepper ═══════════════════════════════════════════════════════════════ */

.tsa-steps {{
    display: flex; align-items: center; gap: 0.5rem;
    margin-bottom: 2.25rem; flex-wrap: wrap;
}}
.tsa-step {{
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.8125rem; color: {INK_FAINT}; font-weight: 500;
}}
.tsa-step-dot {{
    width: 24px; height: 24px; border-radius: 999px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.6875rem; font-weight: 700;
    border: 1px solid {BORDER_STRONG};
    color: {INK_FAINT};
    background: {PAGE};
    flex: none;
}}
.tsa-step.is-current {{ color: {INK}; font-weight: 650; }}
.tsa-step.is-current .tsa-step-dot {{
    background: {INK}; border-color: {INK}; color: {PAGE};
    transform: rotate(-4deg);
    box-shadow: 0 1px 3px rgba(60,46,26,0.3);
}}
.tsa-step.is-done {{ color: {INK_MUTED}; }}
.tsa-step.is-done .tsa-step-dot {{
    background: transparent; border-color: {BORDER_STRONG}; color: {POSITIVE};
}}
.tsa-step-rule {{
    flex: 1 1 12px; min-width: 12px; height: 0;
    border-top: 1px dashed rgba(150, 120, 80, 0.4);
}}

/* ══ Pills ═════════════════════════════════════════════════════════════════ */

.tsa-pill {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    border-radius: 999px; padding: 0.15rem 0.6rem;
    font-size: 0.75rem; font-weight: 600;
    border: 1px solid {BORDER_STRONG};
    color: {INK_MUTED};
    background: {PAGE};
    white-space: nowrap;
}}
.tsa-pill--cover {{
    background: {INK}; border-color: {INK}; color: {PAGE};
    transform: rotate(-1.5deg);
    box-shadow: 0 1px 3px rgba(60,46,26,0.25);
}}
.tsa-pill--strong {{ color: {POSITIVE}; border-color: rgba(31,122,84,0.32); background: rgba(31,122,84,0.08); }}
.tsa-pill--good {{ color: {ACCENT}; border-color: rgba(37,99,235,0.28); background: rgba(37,99,235,0.07); }}
.tsa-pill--maybe {{ color: {CAUTION}; border-color: rgba(138,109,31,0.28); background: rgba(138,109,31,0.08); }}
.tsa-pill--live {{ color: {DANGER}; border-color: rgba(180,50,31,0.3); background: rgba(180,50,31,0.07); }}
.tsa-pill--order {{
    font-variant-numeric: tabular-nums;
    min-width: 1.5rem; justify-content: center; padding: 0.15rem 0.4rem;
}}

/* ══ Photo tiles — taped-in prints ═════════════════════════════════════════ */

div[class*="st-key-tsatile"] {{
    position: relative;
    background: {SURFACE};
    border: 1px solid rgba(150, 120, 80, 0.18);
    border-radius: {RADIUS_TILE};
    padding: 0.7rem 0.7rem 0.8rem 0.7rem;
    box-shadow: 0 1px 2px rgba(60,46,26,0.10), 0 8px 18px -12px rgba(60,46,26,0.45);
    transition: transform 180ms ease, box-shadow 180ms ease;
    transform: rotate(-0.7deg);
}}
div[data-testid="stColumn"]:nth-child(even) div[class*="st-key-tsatile"] {{
    transform: rotate(0.8deg);
}}
div[data-testid="stColumn"]:nth-child(3n) div[class*="st-key-tsatile"] {{
    transform: rotate(-0.35deg);
}}
div[class*="st-key-tsatile"]:hover {{
    transform: rotate(0deg) translateY(-2px);
    box-shadow: 0 2px 4px rgba(60,46,26,0.12), 0 14px 26px -12px rgba(60,46,26,0.5);
    z-index: 2;
}}

/* Washi tape across the top edge */
div[class*="st-key-tsatile"]::before {{
    content: "";
    position: absolute;
    top: -9px; left: 50%;
    width: 62px; height: 19px;
    transform: translateX(-50%) rotate(-2.5deg);
    background:
        repeating-linear-gradient(45deg,
            rgba(255,255,255,0.30) 0 4px, transparent 4px 8px),
        {TAPE};
    border-left: 1px solid rgba(255,255,255,0.35);
    border-right: 1px solid rgba(255,255,255,0.35);
    box-shadow: 0 1px 2px rgba(60,46,26,0.16);
    pointer-events: none;
    z-index: 3;
}}

/* Streamlit nests each image in shrink-to-fit flex wrappers and stamps an inline
   pixel width on the <img>. A percentage width inside a shrink-to-fit ancestor is
   circular and collapses, so every wrapper is given a resolved width and the
   inline width is overridden. */
div[class*="st-key-tsatile"] [data-testid="stElementContainer"],
div[class*="st-key-tsatile"] [data-testid="stFullScreenFrame"],
div[class*="st-key-tsatile"] [data-testid="stImage"],
div[class*="st-key-tsatile"] [data-testid="stImageContainer"],
div[class*="st-key-tsacover"] [data-testid="stElementContainer"],
div[class*="st-key-tsacover"] [data-testid="stFullScreenFrame"],
div[class*="st-key-tsacover"] [data-testid="stImage"],
div[class*="st-key-tsacover"] [data-testid="stImageContainer"] {{
    width: 100% !important;
    max-width: 100% !important;
}}

div[class*="st-key-tsatile"] img {{
    border-radius: 2px;
    aspect-ratio: 4 / 3;
    object-fit: cover;
    width: 100% !important;
    height: auto;
    display: block;
}}

/* The cover is a larger print, tacked down at a gentler angle. */
div[class*="st-key-tsacover"] {{
    position: relative;
    background: {SURFACE};
    padding: 0.85rem 0.85rem 2.6rem 0.85rem;
    border-radius: 3px;
    box-shadow: 0 2px 4px rgba(60,46,26,0.12), 0 22px 44px -20px rgba(60,46,26,0.55);
    transform: rotate(-1deg);
}}
div[class*="st-key-tsacover"]::after {{
    content: "";
    position: absolute;
    top: -11px; left: 22%;
    width: 84px; height: 22px;
    transform: rotate(-4deg);
    background:
        repeating-linear-gradient(45deg,
            rgba(255,255,255,0.3) 0 5px, transparent 5px 10px),
        {TAPE};
    box-shadow: 0 1px 2px rgba(60,46,26,0.18);
    pointer-events: none;
}}
div[class*="st-key-tsacover"] img {{
    border-radius: 2px;
    aspect-ratio: 3 / 2;
    object-fit: cover;
    width: 100% !important;
    height: auto;
    display: block;
}}

div[class*="tsadim"] img {{ opacity: 0.42; filter: saturate(0.5); }}
div[class*="tsadim"]::before {{ opacity: 0.5; }}

/* Tile controls read as quiet affordances, not primary buttons. */
div[class*="st-key-tsatile"] div[data-testid="stHorizontalBlock"] {{
    gap: 0.15rem; margin-top: 0.15rem;
}}
div[class*="st-key-tsatile"] .stButton button {{
    padding: 0.2rem 0.4rem !important;
    font-size: 0.78rem !important;
    min-height: 1.9rem !important;
    background: transparent !important;
    border-color: transparent !important;
    color: {INK_MUTED} !important;
}}
div[class*="st-key-tsatile"] .stButton button:hover:enabled {{
    background: {SURFACE_SUNK} !important;
    border-color: {BORDER} !important;
    color: {INK} !important;
}}
div[class*="st-key-tsatile"] .stButton button:disabled {{ opacity: 0.3 !important; }}

/* ══ Reason text ═══════════════════════════════════════════════════════════ */

.tsa-why {{
    font-size: 0.8125rem !important; line-height: 1.45 !important; color: {INK_MUTED};
    margin: 0.4rem 0 0.15rem 0;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
}}
.tsa-why--cover {{
    font-size: 0.9375rem !important; line-height: 1.55 !important; color: {INK_MUTED};
    -webkit-line-clamp: 4; margin-top: 0.6rem;
}}

/* ══ Divider ═══════════════════════════════════════════════════════════════ */

.tsa-rule {{
    border: 0;
    border-top: 1px dashed rgba(150, 120, 80, 0.38);
    margin: 2.5rem 0 1.75rem 0;
}}

/* ══ Facebook preview — deliberately NOT journal-styled ════════════════════ */

.tsa-fb {{
    background: #FFFFFF;
    border: 1px solid #DDDFE2;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 6px rgba(60,46,26,0.14), 0 16px 34px -20px rgba(60,46,26,0.4);
    font-family: {FONT_STACK};
}}
.tsa-fb-head {{ display: flex; align-items: center; gap: 0.65rem; padding: 0.9rem 1rem 0.65rem 1rem; }}
.tsa-fb-avatar {{
    width: 40px; height: 40px; border-radius: 999px;
    background: #E4E6EB; border: 1px solid #DDDFE2;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; color: #65676B; font-size: 0.9rem; flex: none;
}}
.tsa-fb-name {{ font-size: 0.875rem; font-weight: 650; color: #050505; line-height: 1.3; }}
.tsa-fb-time {{ font-size: 0.75rem; color: #65676B; }}
.tsa-fb-body {{
    padding: 0 1rem 0.85rem 1rem;
    font-size: 0.9375rem; line-height: 1.55; color: #050505;
    white-space: normal;   /* newlines arrive as <br>; pre-wrap would double them */
}}
/* Preview photos stay square-cornered and untaped. */
div[class*="st-key-tsatile-fb"] {{
    transform: none !important; border: 0 !important;
    box-shadow: none !important; padding: 0 !important;
    background: transparent !important; border-radius: 0 !important;
}}
div[class*="st-key-tsatile-fb"]::before {{ display: none !important; }}
div[class*="st-key-tsatile-fb"] img {{ border-radius: 0 !important; }}

/* ══ Empty state ═══════════════════════════════════════════════════════════ */

.tsa-empty {{
    border: 1px dashed {BORDER_STRONG};
    border-radius: 8px;
    padding: 2.75rem 2rem;
    text-align: center;
    background: rgba(255,255,255,0.5);
}}
.tsa-empty-title {{ font-size: 1rem; font-weight: 650; color: {INK}; margin-bottom: 0.3rem; }}
.tsa-empty-body {{ font-size: 0.875rem; color: {INK_MUTED}; max-width: 44ch; margin: 0 auto; }}

/* ══ Widgets ═══════════════════════════════════════════════════════════════ */

.stTextArea textarea, .stTextInput input {{
    background: rgba(255,255,255,0.72) !important;
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_CONTROL} !important;
    color: {INK} !important;
    font-size: 0.9375rem !important;
    line-height: 1.6 !important;
}}
.stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: {BORDER_STRONG} !important;
    background: #FFFFFF !important;
    box-shadow: 0 0 0 3px rgba(150,120,80,0.14) !important;
}}
.stTextArea textarea::placeholder {{ color: {INK_FAINT} !important; }}

.stButton button {{
    border-radius: {RADIUS_CONTROL} !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    transition: background 140ms ease, border-color 140ms ease, transform 140ms ease !important;
}}
.stButton button[kind="primary"] {{
    background: {INK} !important;
    border: 1px solid {INK} !important;
    color: {PAGE} !important;
    padding: 0.55rem 1.2rem !important;
    box-shadow: 0 2px 5px rgba(60,46,26,0.28) !important;
}}
.stButton button[kind="primary"]:hover:enabled {{
    background: #17130F !important;
    transform: translateY(-1px);
}}
.stButton button[kind="secondary"] {{
    background: rgba(255,255,255,0.6) !important;
    border: 1px solid {BORDER_STRONG} !important;
    color: {INK} !important;
}}
.stButton button[kind="secondary"]:hover:enabled {{ background: #FFFFFF !important; }}
.stButton button:disabled {{ opacity: 0.42 !important; }}

div[data-testid="stExpander"] details {{
    border: 1px dashed {BORDER_STRONG} !important;
    border-radius: 8px !important;
    background: rgba(255,255,255,0.45) !important;
}}
div[data-testid="stExpander"] summary {{ font-size: 0.875rem !important; color: {INK_MUTED} !important; }}

/* ══ Page-turn ═════════════════════════════════════════════════════════════ */

.tsa-turn {{
    position: fixed;
    inset: 0;
    z-index: 9999;
    pointer-events: none;   /* never intercepts a click, at any point */
    transform-origin: left center;
    background:
        linear-gradient(90deg,
            rgba(120,96,60,0.22) 0%,
            rgba(255,255,255,0.06) 12%,
            {PAGE} 45%,
            {PAGE} 100%);
    box-shadow: 12px 0 34px -8px rgba(60,46,26,0.5);
    will-change: transform, opacity;
}}

@media (prefers-reduced-motion: reduce) {{
    .tsa-turn {{ display: none !important; }}
    [data-testid="stMain"] .block-container {{ animation: none !important; }}
}}

/* ══ Responsive ════════════════════════════════════════════════════════════ */

@media (max-width: 900px) {{
    [data-testid="stMain"] .block-container {{
        margin-top: 0.5rem;
        padding: 1.5rem 1.15rem 2.5rem 1.6rem;
        border-radius: 2px 8px 8px 2px;
    }}
    [data-testid="stMain"] .block-container::after {{ left: 16px; }}
    [data-testid="stMain"] .block-container::before {{ width: 12px; }}
    .tsa-display {{ font-size: 2.5rem; }}
    .tsa-title {{ font-size: 1.85rem; }}
    .tsa-steps {{ gap: 0.35rem; }}
    .tsa-step-label {{ display: none; }}
    .tsa-step.is-current .tsa-step-label {{ display: inline; }}
    div[class*="st-key-tsacover"] img {{ aspect-ratio: 4 / 3; }}
    div[class*="st-key-tsatile"], div[class*="st-key-tsacover"] {{ transform: none !important; }}
}}
</style>
"""


def inject() -> None:
    """Inject the global stylesheet. Call once, immediately after set_page_config."""
    st.markdown(_STYLES, unsafe_allow_html=True)


def page_turn(nonce: str) -> None:
    """Play the page-turn transition exactly once.

    Streamlit destroys and rebuilds the DOM on every rerun, so a CSS animation
    declared on a persistent selector would replay on *every* interaction — the
    page would flap each time a slider moved. Instead the caller supplies a
    nonce that changes only when the step changes; the unique animation name it
    produces is what makes the browser treat this as a new animation and play it.

    Args:
        nonce: Token unique to this transition.
    """
    st.markdown(
        f"""
<style>
@keyframes tsaSheet-{nonce} {{
    0%   {{ transform: perspective(1600px) rotateY(0deg);   opacity: 1; }}
    70%  {{ opacity: 1; }}
    100% {{ transform: perspective(1600px) rotateY(-105deg); opacity: 0; }}
}}
@keyframes tsaSettle-{nonce} {{
    0%   {{ opacity: 0; transform: perspective(1600px) rotateY(6deg) translateX(14px); }}
    100% {{ opacity: 1; transform: none; }}
}}
.tsa-turn {{ animation: tsaSheet-{nonce} 620ms cubic-bezier(.36,.06,.28,1) forwards; }}
[data-testid="stMain"] .block-container {{
    animation: tsaSettle-{nonce} 560ms cubic-bezier(.22,.61,.36,1) both;
    transform-origin: left center;
}}
</style>
<div class="tsa-turn"></div>
""",
        unsafe_allow_html=True,
    )
