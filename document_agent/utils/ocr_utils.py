"""
ocr_utils.py
------------
Dual-pass pytesseract OCR for Nepal NIN documents.

Pass 1 (nep only)   → optimised for Devanagari fields
                       आवेदन नम्बर, राष्ट्रिय परिचय नम्बर, ई.सं.
Pass 2 (nep + eng)  → optimised for mixed / English / digit fields
                       First name, Last name, application number digits

Both outputs are merged into a single text block sent to the LLM,
letting Gemini pick the best value per field.
"""

from __future__ import annotations
import cv2
import numpy as np
import pytesseract
from PIL import Image
from config import get_settings

TESSERACT_CMD = get_settings().tesseract_cmd
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

TESS_CONFIG_NEP      = r"--oem 1 --psm 6 -l nep"
TESS_CONFIG_COMBINED = r"--oem 1 --psm 6 -l nep+eng"


def _pil_to_bgr(pil_img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _preprocess_for_ocr(img_bgr: np.ndarray) -> Image.Image:
    """
    Grayscale → bilateral filter (removes noise, keeps edges)
    → Otsu threshold → return as PIL for pytesseract.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


def run_ocr_dual_pass(pil_image: Image.Image) -> dict[str, str]:
    """
    Run both OCR passes on a single PIL image.

    Returns
    -------
    dict with keys:
        "nep_pass"      – Devanagari-only OCR output
        "combined_pass" – nep+eng OCR output
    """
    img_bgr      = _pil_to_bgr(pil_image)
    preprocessed = _preprocess_for_ocr(img_bgr)

    text_nep      = pytesseract.image_to_string(preprocessed, config=TESS_CONFIG_NEP)
    text_combined = pytesseract.image_to_string(preprocessed, config=TESS_CONFIG_COMBINED)

    return {
        "nep_pass":      text_nep.strip(),
        "combined_pass": text_combined.strip(),
    }


def merge_ocr_passes(ocr_result: dict[str, str]) -> str:
    """
    Concatenate both passes into a single labelled block.
    The LLM sees both and uses whichever is cleaner per field.
    """
    return (
        "=== Nepali pass ===\n"
        + ocr_result["nep_pass"]
        + "\n\n=== Combined pass ===\n"
        + ocr_result["combined_pass"]
    )
