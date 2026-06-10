"""
pdf_utils.py
------------
Converts PDF bytes / file paths into PIL images using pdf2image + Poppler.
Poppler v26.02.0 is already installed on this machine.

For Windows, set POPPLER_BIN_PATH to your poppler bin folder, e.g.:
    r"C:/tools/poppler/Library/bin"
"""

from __future__ import annotations
import io
from pathlib import Path
from PIL import Image
from config import get_settings

# Set this if Poppler is not on PATH (common on Windows)
POPPLER_BIN_PATH: str | None = get_settings().poppler_path or None

try:
    from pdf2image import convert_from_bytes, convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


def _check_available() -> None:
    if not PDF2IMAGE_AVAILABLE:
        raise RuntimeError(
            "pdf2image is not installed. "
            "Run: pip install pdf2image"
        )


def pdf_bytes_to_images(pdf_bytes: bytes, dpi: int = 300) -> list[Image.Image]:
    """Convert raw PDF bytes → list of PIL Images (one per page)."""
    _check_available()
    return convert_from_bytes(
        pdf_bytes,
        dpi=dpi,
        poppler_path=POPPLER_BIN_PATH,
        fmt="jpeg",
    )


def pdf_path_to_images(pdf_path: str | Path, dpi: int = 300) -> list[Image.Image]:
    """Convert a PDF file path → list of PIL Images (one per page)."""
    _check_available()
    return convert_from_path(
        str(pdf_path),
        dpi=dpi,
        poppler_path=POPPLER_BIN_PATH,
        fmt="jpeg",
    )


def image_bytes_to_pil(image_bytes: bytes) -> Image.Image:
    """Decode raw image bytes (JPEG / PNG) into a PIL Image."""
    return Image.open(io.BytesIO(image_bytes))
