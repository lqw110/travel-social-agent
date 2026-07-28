"""Run story analysis and photo scoring from the terminal, without the UI.

Useful for seeing the raw scores and reasons the vision model returns before
they are turned into "Strong match" / "Good match" labels in the app.

Usage
-----
    python scripts/try_photo_scoring.py
    python scripts/try_photo_scoring.py --folder ~/Pictures/istanbul

Costs one OpenAI call for the story plus one per photo. Start with a small
folder.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from src.config import config  # noqa: E402

DEFAULT_STORY = """
I went to Istanbul last spring and stumbled upon a whirling dervish ceremony
in a 16th-century lodge. The silence in the room was unlike anything I've felt —
everyone watching in complete stillness as the dervishes spun in white robes
under soft golden light. Afterwards we wandered through the spice bazaar and
tried simit from a street vendor near the Galata Bridge.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", default=str(ROOT / "data" / "photos"))
    parser.add_argument("--story", default=DEFAULT_STORY)
    parser.add_argument("--max", type=int, default=5, help="photos to select")
    args = parser.parse_args()

    if not config.OPENAI_API_KEY:
        print("OPENAI_API_KEY is not set. Add it to .env and try again.")
        return 1

    from src.agents.photo_ranker import score_image_relevance
    from src.agents.story_analyzer import analyze_story
    from src.tools.image_tools import scan_local_images, select_best_images

    print("=" * 60)
    print("1. Reading the story")
    print("=" * 60)
    analysis = analyze_story(args.story)
    print(f"  Location    : {analysis['location']}")
    print(f"  Main event  : {analysis['main_event']}")
    print(f"  Tone        : {analysis['emotional_tone']}")
    print(f"  Look for    : {', '.join(analysis['key_objects_scenes'])}")

    print("\n" + "=" * 60)
    print(f"2. Scanning {args.folder}")
    print("=" * 60)
    try:
        candidates = scan_local_images(args.folder)
    except FileNotFoundError as exc:
        print(f"  {exc}")
        return 1

    if not candidates:
        print("  No photos found. Add some images and try again.")
        return 0
    print(f"  {len(candidates)} photo(s) found")

    print("\n" + "=" * 60)
    print("3. Scoring each photo")
    print("=" * 60)
    ranked = []
    for i, cand in enumerate(candidates, start=1):
        print(f"  [{i}/{len(candidates)}] {cand['filename']}", flush=True)
        try:
            result = score_image_relevance(cand["path"], dict(analysis), args.story)
            ranked.append(result)
            print(f"        {result['relevance_score']:.1f}/10 — {result['reason']}")
        except Exception as exc:
            print(f"        skipped: {exc}")

    print("\n" + "=" * 60)
    print("4. Selected for the post")
    print("=" * 60)
    for rank, img in enumerate(select_best_images(ranked, max_images=args.max), start=1):
        bar = "#" * int(round(img["relevance_score"]))
        print(f"  {rank}. {img['filename']:<28} {img['relevance_score']:.1f} {bar}")
        print(f"     {img['reason']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
