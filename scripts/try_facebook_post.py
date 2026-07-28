"""Verify Facebook posting end to end, without going through the UI.

Usage
-----
    python scripts/try_facebook_post.py             # dry run, posts nothing
    python scripts/try_facebook_post.py --live      # real text-only post
    python scripts/try_facebook_post.py --live --photos   # real post with photos

Defaults to a dry run. --live asks for confirmation before anything is sent.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from src.config import config  # noqa: E402
from src.tools.facebook_tool import get_page_identity, post_to_facebook_page  # noqa: E402
from src.tools.image_tools import scan_local_images  # noqa: E402

TEST_CAPTION = "Testing my Travel Social Agent — please ignore, just checking the pipeline works."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="actually publish")
    parser.add_argument("--photos", action="store_true", help="attach photos")
    parser.add_argument("--folder", default=str(ROOT / "data" / "photos"))
    parser.add_argument("--max", type=int, default=2, help="how many photos")
    args = parser.parse_args()

    if not config.FACEBOOK_PAGE_ID or not config.FACEBOOK_PAGE_ACCESS_TOKEN:
        print("Facebook credentials are missing from .env.")
        print("Run:  python scripts/check_facebook_credentials.py --write-env")
        return 1

    identity = get_page_identity()
    print("=" * 60)
    print(f"  Mode   : {'LIVE — will publish' if args.live else 'dry run — publishes nothing'}")
    print(f"  Page   : {identity['name']} ({config.FACEBOOK_PAGE_ID})")
    print(f"  Photos : {'yes' if args.photos else 'no'}")
    print("=" * 60)

    if not identity["connected"]:
        print(f"\n  Cannot reach that Page: {identity.get('error')}")
        print("  Run:  python scripts/check_facebook_credentials.py")
        if args.live:
            return 1

    image_paths = []
    if args.photos:
        candidates = scan_local_images(args.folder)
        image_paths = [c["path"] for c in candidates[: args.max]]
        if not image_paths:
            print(f"\n  No photos in {args.folder}")
            return 1
        print("\n  Attaching:")
        for p in image_paths:
            print(f"    - {Path(p).name}")

    print(f"\n  Caption: {TEST_CAPTION}\n")

    if args.live:
        if input('  Type "YES" to publish this for real: ').strip() != "YES":
            print("  Cancelled.")
            return 0

    result = post_to_facebook_page(
        message=TEST_CAPTION,
        image_paths=image_paths or None,
        dry_run=not args.live,
    )

    print("\n" + "=" * 60)
    if result.get("success") and result.get("dry_run"):
        print("  Dry run finished. This is what would have been sent:")
        print(json.dumps(result["payload"], indent=2))
    elif result.get("success"):
        print(f"  Published. Post ID: {result['post_id']}")
    else:
        print("  Failed:")
        print(json.dumps(result.get("error"), indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
