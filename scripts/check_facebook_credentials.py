"""Check which Facebook Page your token can post to, and optionally save it.

Facebook's Graph API Explorer hands you a *User* token, but posting to a Page
needs that Page's own token. This script exchanges one for the other.

Usage
-----
    python scripts/check_facebook_credentials.py              # inspect only
    python scripts/check_facebook_credentials.py --write-env  # save to .env

Tokens are printed redacted on purpose. People screenshot terminal output when
asking for help, and a Page access token in a screenshot is a live credential.
Use --write-env to put the real value straight into your .env instead.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import requests  # noqa: E402

from src.config import config  # noqa: E402

GRAPH = f"https://graph.facebook.com/{config.GRAPH_API_VERSION}"


def redact(secret: str) -> str:
    """Show only enough of a token to tell two apart."""
    if not secret:
        return "(empty)"
    if len(secret) <= 10:
        return "*" * len(secret)
    return f"{secret[:4]}…{secret[-4:]}  ({len(secret)} chars)"


def write_env(page_id: str, page_token: str) -> None:
    """Replace the Page ID and token lines in .env, leaving everything else."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        print(f"\n  No .env found at {env_path}. Copy .env.example to .env first.")
        return

    lines = env_path.read_text().splitlines()
    updated, seen = [], set()
    for line in lines:
        if line.startswith("FACEBOOK_PAGE_ID="):
            updated.append(f"FACEBOOK_PAGE_ID={page_id}")
            seen.add("id")
        elif line.startswith("FACEBOOK_PAGE_ACCESS_TOKEN="):
            updated.append(f"FACEBOOK_PAGE_ACCESS_TOKEN={page_token}")
            seen.add("token")
        else:
            updated.append(line)
    if "id" not in seen:
        updated.append(f"FACEBOOK_PAGE_ID={page_id}")
    if "token" not in seen:
        updated.append(f"FACEBOOK_PAGE_ACCESS_TOKEN={page_token}")

    env_path.write_text("\n".join(updated) + "\n")
    print(f"\n  Saved Page ID and token to {env_path}")


def main() -> int:
    token = config.FACEBOOK_PAGE_ACCESS_TOKEN
    if not token:
        print("FACEBOOK_PAGE_ACCESS_TOKEN is not set in .env.")
        print("Paste the token from Graph API Explorer there first, then re-run.")
        return 1

    print("=" * 60)
    print("FACEBOOK CREDENTIAL CHECK")
    print("=" * 60)
    print(f"  API version : {config.GRAPH_API_VERSION}")
    print(f"  Token in .env: {redact(token)}")

    print("\n1. Who does this token belong to?")
    resp = requests.get(f"{GRAPH}/me", params={"access_token": token, "fields": "id,name"}, timeout=15)
    me = resp.json()
    if "error" in me:
        print(f"   Rejected: {me['error'].get('message')}")
        print("\n   If it says the session expired, generate a fresh token in")
        print("   Graph API Explorer and paste it into .env.")
        return 1
    print(f"   {me.get('name')} (id {me.get('id')})")

    print("\n2. Which Pages can it manage?")
    resp = requests.get(f"{GRAPH}/me/accounts", params={"access_token": token}, timeout=15)
    data = resp.json()

    if "error" in data:
        print(f"   Rejected: {data['error'].get('message')}")
        return 1

    pages = data.get("data", [])
    if not pages:
        print("   None.")
        print("\n   Your token is missing the Page permissions. In Graph API Explorer add")
        print("   both pages_manage_posts and pages_read_engagement, then regenerate.")
        return 1

    for i, page in enumerate(pages):
        print(f"\n   [{i}] {page.get('name')}")
        print(f"       Page ID : {page.get('id')}")
        print(f"       Token   : {redact(page.get('access_token', ''))}")

    if "--write-env" in sys.argv:
        choice = 0
        if len(pages) > 1:
            raw = input(f"\nWhich Page? [0-{len(pages) - 1}]: ").strip()
            if not raw.isdigit() or int(raw) >= len(pages):
                print("Not a valid choice.")
                return 1
            choice = int(raw)
        page = pages[choice]
        write_env(page["id"], page["access_token"])
        print("  You can now run:  python scripts/try_facebook_post.py")
    else:
        print("\n  Re-run with --write-env to save one of these into your .env.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
