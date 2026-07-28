"""Tests for image scanning tools."""

import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from src.tools.image_tools import scan_local_images, select_best_images


def _make_image(folder: Path, name: str) -> Path:
    path = folder / name
    img = Image.new("RGB", (100, 80), color=(128, 64, 32))
    img.save(path)
    return path


def test_scan_returns_candidates(tmp_path: Path) -> None:
    _make_image(tmp_path, "photo1.jpg")
    _make_image(tmp_path, "photo2.png")
    candidates = scan_local_images(str(tmp_path))
    assert len(candidates) == 2
    filenames = {c["filename"] for c in candidates}
    assert "photo1.jpg" in filenames
    assert "photo2.png" in filenames


def test_scan_ignores_unsupported_extensions(tmp_path: Path) -> None:
    _make_image(tmp_path, "photo.jpg")
    (tmp_path / "document.pdf").write_bytes(b"%PDF")
    candidates = scan_local_images(str(tmp_path))
    assert len(candidates) == 1


def test_scan_missing_folder_raises() -> None:
    with pytest.raises(FileNotFoundError):
        scan_local_images("/nonexistent/path/12345")


def test_scan_includes_metadata(tmp_path: Path) -> None:
    _make_image(tmp_path, "photo.jpg")
    candidates = scan_local_images(str(tmp_path))
    c = candidates[0]
    assert c["width"] == 100
    assert c["height"] == 80
    assert c["size_bytes"] > 0


def test_select_best_images_limits_count() -> None:
    ranked = [
        {"path": f"/p{i}.jpg", "filename": f"p{i}.jpg", "relevance_score": float(i), "reason": ""}
        for i in range(10)
    ]
    selected = select_best_images(ranked, max_images=3)
    assert len(selected) == 3
    # Should be top 3 scores: 9, 8, 7
    scores = [s["relevance_score"] for s in selected]
    assert scores == [9.0, 8.0, 7.0]
