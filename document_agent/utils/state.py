from typing import TypedDict
import numpy as np


class DocumentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────
    image_path:          str          # file-path mode (intake_agent standalone)
    file_bytes:          bytes        # HTTP upload mode (pipeline)
    file_type:           str          # "pdf" | "image"

    # ── Blur-check ─────────────────────────────────────────────────────
    image_array:         np.ndarray | None
    gray_array:          np.ndarray | None
    laplacian_variance:  float
    fft_energy:          float
    regional_scores:     list[float]
    blur_score:          float
    verdict:             str          # "blurry" | "borderline" | "clear"
    confidence:          float
    reason:              str
    reupload_message:    str

    # ── OCR ────────────────────────────────────────────────────────────
    ocr_text:            str          # merged dual-pass output
    ocr_error:           str

    # ── LLM Extraction ─────────────────────────────────────────────────
    extraction_prompt:   str
    extracted_fields:    dict         # parsed JSON from Gemini
    extraction_error:    str

    # ── Final report ───────────────────────────────────────────────────
    report:              dict


# Alias so existing intake_agent.py imports keep working without changes
ImageState = DocumentState
