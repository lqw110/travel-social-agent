"""Tools for scanning and processing local image files."""

import logging
import io
from pathlib import Path

from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

from src.config import config
from src.state import ImageCandidate

logger = logging.getLogger(__name__)

HEIC_EXTENSIONS = {".heic", ".heif"}


def scan_local_images(folder_path: str) -> list[ImageCandidate]:
    """Scan a local folder and return metadata for all supported images.

    Args:
        folder_path: Absolute or relative path to the folder containing photos.

    Returns:
        List of ImageCandidate dicts with path, filename, size, and dimensions.
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Photo folder not found: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")

    candidates: list[ImageCandidate] = []

    for ext in config.SUPPORTED_IMAGE_EXTENSIONS:
        for image_path in folder.glob(f"*{ext}"):
            candidates.append(_build_candidate(image_path))
        for image_path in folder.glob(f"*{ext.upper()}"):
            candidates.append(_build_candidate(image_path))

    # Deduplicate by resolved path (glob may return duplicates on case-insensitive FS)
    seen: set[str] = set()
    unique: list[ImageCandidate] = []
    for c in candidates:
        resolved = str(Path(c["path"]).resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique.append(c)

    logger.info("Found %d images in %s", len(unique), folder_path)
    return unique


def _build_candidate(image_path: Path) -> ImageCandidate:
    """Build an ImageCandidate from a Path, reading basic metadata."""
    size_bytes = image_path.stat().st_size
    width, height = None, None
    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception as exc:
        logger.warning("Could not read dimensions for %s: %s", image_path, exc)

    return ImageCandidate(
        path=str(image_path.resolve()),
        filename=image_path.name,
        size_bytes=size_bytes,
        width=width,
        height=height,
    )


def load_image_as_jpeg_bytes(image_path: str) -> bytes:
    """Load any supported image (including HEIC) and return it as JPEG bytes.

    OpenAI Vision does not accept HEIC files directly, so HEIC/HEIF images
    are converted to JPEG in memory before being sent to the API.

    Args:
        image_path: Path to the source image file.

    Returns:
        JPEG-encoded bytes ready for base64 encoding.
    """
    path = Path(image_path)
    ext = path.suffix.lower()

    if ext in HEIC_EXTENSIONS:
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            raise ImportError(
                "pillow-heif is required to read HEIC files.\n"
                "Install it with:  pip install pillow-heif"
            )

    with Image.open(path) as img:
        # Convert to RGB (HEIC can be in various modes; JPEG requires RGB)
        rgb = img.convert("RGB")
        buffer = io.BytesIO()
        rgb.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()


def select_best_images(
    ranked_images: list[dict],
    max_images: int = 5,
    min_score: float = 6.5,
) -> list[dict]:
    """Select the top-ranked images that meet the minimum relevance threshold.

    Args:
        ranked_images: List of RankedImage dicts.
        max_images: Maximum number of images to return.
        min_score: Minimum relevance score (1–10) to be included.
                   Images below this threshold are excluded even if they
                   are the highest-scoring ones available.

    Returns:
        Filtered list of images that are both above the threshold and top-ranked.
    """
    above_threshold = [
        img for img in ranked_images if img["relevance_score"] >= min_score
    ]
    sorted_images = sorted(
        above_threshold, key=lambda x: x["relevance_score"], reverse=True
    )
    selected = sorted_images[:max_images]
    logger.info(
        "Image selection: %d candidates, %d above threshold (%.1f), %d selected",
        len(ranked_images), len(above_threshold), min_score, len(selected)
    )
    return selected
