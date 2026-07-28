"""Tool for posting to a Facebook Page via the Meta Graph API."""

import logging
from pathlib import Path
from typing import Any, Optional

import requests

from src.config import config

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com"


def get_page_identity() -> dict[str, Any]:
    """Read the connected Page's display name so the UI can name it explicitly.

    Read-only. Never raises — a failure returns a neutral fallback so the
    publishing screen can still render and report the problem.

    Returns:
        Dict with 'connected' (bool), 'name', 'id', and optional 'error'.
    """
    if not config.FACEBOOK_PAGE_ID or not config.FACEBOOK_PAGE_ACCESS_TOKEN:
        return {"connected": False, "name": "No Page connected", "id": "", "error": "missing_credentials"}

    url = f"{GRAPH_BASE}/{config.GRAPH_API_VERSION}/{config.FACEBOOK_PAGE_ID}"
    try:
        response = requests.get(
            url,
            params={"fields": "name", "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN},
            timeout=10,
        )
        data = response.json()
    except Exception as exc:
        logger.warning("Could not read Page identity: %s", exc)
        return {"connected": False, "name": "Facebook Page", "id": config.FACEBOOK_PAGE_ID, "error": str(exc)}

    if response.ok and "name" in data:
        return {"connected": True, "name": data["name"], "id": data.get("id", config.FACEBOOK_PAGE_ID)}

    logger.warning("Page identity lookup failed: %s", data)
    return {
        "connected": False,
        "name": "Facebook Page",
        "id": config.FACEBOOK_PAGE_ID,
        "error": data.get("error", {}).get("message", "unknown"),
    }


def post_to_facebook_page(
    message: str,
    image_paths: Optional[list[str]] = None,
    dry_run: Optional[bool] = None,
) -> dict[str, Any]:
    """Post a message (and optionally images) to the configured Facebook Page.

    Args:
        message: The caption / post text.
        image_paths: Optional list of local image file paths to attach.
        dry_run: If True (default from config), log the payload but do not call the API.

    Returns:
        Dict with 'success', 'post_id' (if live), and 'payload' (for dry-run inspection).
    """
    is_dry_run = dry_run if dry_run is not None else config.DRY_RUN

    if is_dry_run:
        payload = {
            "page_id": config.FACEBOOK_PAGE_ID,
            "message": message,
            "image_paths": image_paths or [],
        }
        logger.info("[DRY RUN] Would post to Facebook Page: %s", payload)
        return {"success": True, "dry_run": True, "payload": payload, "post_id": None}

    if image_paths:
        return _post_with_photos(message, image_paths)
    return _post_text(message)


def _post_text(message: str) -> dict[str, Any]:
    """Post a text-only update to the Facebook Page feed."""
    url = f"{GRAPH_BASE}/{config.GRAPH_API_VERSION}/{config.FACEBOOK_PAGE_ID}/feed"
    response = requests.post(
        url,
        data={"message": message, "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN},
        timeout=30,
    )
    data = response.json()
    if response.ok and "id" in data:
        logger.info("Posted successfully. Post ID: %s", data["id"])
        return {"success": True, "dry_run": False, "post_id": data["id"], "payload": data}

    logger.error("Facebook API error: %s", data)
    return {"success": False, "dry_run": False, "error": data, "post_id": None}


def _upload_photo(image_path: str) -> Optional[str]:
    """Upload a single photo as unpublished and return its media_fbid.

    The photo is uploaded with published=false so it doesn't appear on the
    Page until we explicitly attach it to a feed post.

    Args:
        image_path: Local file path to the image.

    Returns:
        media_fbid string if successful, None if upload failed.
    """
    from src.tools.image_tools import load_image_as_jpeg_bytes

    url = f"{GRAPH_BASE}/{config.GRAPH_API_VERSION}/{config.FACEBOOK_PAGE_ID}/photos"
    filename = Path(image_path).name

    try:
        jpeg_bytes = load_image_as_jpeg_bytes(image_path)
    except Exception as exc:
        logger.error("Could not read image %s: %s", filename, exc)
        return None

    response = requests.post(
        url,
        data={
            "published": "false",
            "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        },
        files={"source": (filename, jpeg_bytes, "image/jpeg")},
        timeout=60,
    )
    data = response.json()
    if response.ok and "id" in data:
        logger.info("Uploaded photo %s → media_fbid=%s", filename, data["id"])
        return data["id"]

    logger.error("Photo upload failed for %s: %s", filename, data)
    return None


def _post_with_photos(message: str, image_paths: list[str]) -> dict[str, Any]:
    """Upload photos then publish a multi-photo feed post.

    Flow:
      1. Upload each image as unpublished → get media_fbid
      2. Create a feed post with attached_media[] referencing those fbids
    """
    logger.info("Uploading %d photo(s)…", len(image_paths))
    media_fbids: list[str] = []
    for path in image_paths:
        fbid = _upload_photo(path)
        if fbid:
            media_fbids.append(fbid)

    if not media_fbids:
        logger.warning("No photos uploaded successfully — falling back to text-only post.")
        return _post_text(message)

    # Build attached_media list for the feed post
    # Meta requires each entry as a separate form field: attached_media[0], attached_media[1]…
    url = f"{GRAPH_BASE}/{config.GRAPH_API_VERSION}/{config.FACEBOOK_PAGE_ID}/feed"
    data: dict[str, Any] = {
        "message": message,
        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
    }
    for i, fbid in enumerate(media_fbids):
        data[f"attached_media[{i}]"] = f'{{"media_fbid":"{fbid}"}}'

    response = requests.post(url, data=data, timeout=30)
    result = response.json()

    if response.ok and "id" in result:
        logger.info("Photo post published. Post ID: %s", result["id"])
        return {
            "success": True,
            "dry_run": False,
            "post_id": result["id"],
            "photos_uploaded": len(media_fbids),
            "payload": result,
        }

    logger.error("Feed post failed: %s", result)
    return {"success": False, "dry_run": False, "error": result, "post_id": None}
