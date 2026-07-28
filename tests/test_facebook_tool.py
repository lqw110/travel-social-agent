"""Tests for the Facebook posting tool."""

from src.tools.facebook_tool import post_to_facebook_page


def test_dry_run_does_not_call_api() -> None:
    result = post_to_facebook_page("Hello world", dry_run=True)
    assert result["success"] is True
    assert result["dry_run"] is True
    assert result["post_id"] is None


def test_dry_run_payload_contains_message() -> None:
    result = post_to_facebook_page("My Istanbul trip", image_paths=["/a.jpg"], dry_run=True)
    assert result["payload"]["message"] == "My Istanbul trip"
    assert "/a.jpg" in result["payload"]["image_paths"]
