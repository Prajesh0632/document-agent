"""
ocr_agent.py
------------
LangGraph node: runs dual-pass pytesseract OCR on the uploaded document.

Input  (from DocumentState): file_bytes, file_type ("pdf" | "image")
Output (to DocumentState)  : ocr_text (merged dual-pass), ocr_error
"""

from __future__ import annotations
import logging
from PIL import Image

from document_agent.utils.state import DocumentState
from document_agent.utils.ocr_utils import run_ocr_dual_pass, merge_ocr_passes
from document_agent.utils.pdf_utils import pdf_bytes_to_images, image_bytes_to_pil

logger = logging.getLogger(__name__)


def run_ocr(state: DocumentState) -> DocumentState:
    """
    LangGraph node — reads file_bytes from state, runs dual-pass OCR,
    and writes merged text back into state["ocr_text"].

    For PDFs, only the first page is processed (NIN docs are single-page).
    """
    file_bytes: bytes = state.get("file_bytes", b"")
    file_type:  str   = state.get("file_type", "image")

    if not file_bytes:
        return {
            **state,
            "ocr_text":  "",
            "ocr_error": "No file bytes available in state.",
        }

    try:
        if file_type == "pdf":
            logger.info("Converting PDF to image (first page, 300 dpi)...")
            pages: list[Image.Image] = pdf_bytes_to_images(file_bytes, dpi=300)
            if not pages:
                raise ValueError("PDF conversion produced no pages.")
            pil_image = pages[0]
        else:
            pil_image = image_bytes_to_pil(file_bytes)

        logger.info("Running dual-pass OCR...")
        ocr_result   = run_ocr_dual_pass(pil_image)
        merged_text  = merge_ocr_passes(ocr_result)

        logger.info(
            "OCR complete. nep_pass=%d chars, combined_pass=%d chars",
            len(ocr_result["nep_pass"]),
            len(ocr_result["combined_pass"]),
        )

        return {
            **state,
            "ocr_text":  merged_text,
            "ocr_error": "",
        }

    except Exception as exc:
        logger.error("OCR failed: %s", exc, exc_info=True)
        return {
            **state,
            "ocr_text":  "",
            "ocr_error": str(exc),
        }
