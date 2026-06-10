"""
tests/test_pipeline.py
----------------------
Quick smoke-tests for each stage of the NIN pipeline.

Run with:
    python -m pytest tests/ -v
    # or run a single test:
    python tests/test_pipeline.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_blank_jpeg_bytes(width: int = 200, height: int = 200) -> bytes:
    """Create a minimal solid-white JPEG in memory (no file needed)."""
    try:
        from PIL import Image
        import io
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        raise RuntimeError("Pillow is required for tests: pip install Pillow")


def _make_sharp_jpeg_bytes() -> bytes:
    """Create a JPEG with high-frequency content (checkerboard = sharp)."""
    try:
        import numpy as np
        from PIL import Image
        import io
        arr = np.indices((200, 200)).sum(axis=0) % 2 * 255
        img = Image.fromarray(arr.astype("uint8"), mode="L").convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        raise RuntimeError("numpy + Pillow required for sharp image test.")


# ── Tests ────────────────────────────────────────────────────────────────────

def test_state_imports():
    """DocumentState and ImageState should be importable and identical."""
    from document_agent.utils.state import DocumentState, ImageState
    assert DocumentState is ImageState, "ImageState alias broken"
    print("[PASS] test_state_imports")


def test_prompt_content():
    """NIN extraction prompt should contain all five field names."""
    from document_agent.prompts.nin_prompt import NIN_EXTRACTION_PROMPT
    for field in ["application_number", "nin", "first_name", "last_name", "dob_ad"]:
        assert field in NIN_EXTRACTION_PROMPT, f"Missing field in prompt: {field}"
    print("[PASS] test_prompt_content")


def test_merge_ocr_passes():
    """merge_ocr_passes should produce a labelled string."""
    from document_agent.utils.ocr_utils import merge_ocr_passes
    result = merge_ocr_passes({"nep_pass": "नेपाली", "combined_pass": "English"})
    assert "=== Nepali pass ===" in result
    assert "=== Combined pass ===" in result
    assert "नेपाली" in result
    assert "English" in result
    print("[PASS] test_merge_ocr_passes")


def test_image_bytes_to_pil():
    """image_bytes_to_pil should return a valid PIL Image."""
    from document_agent.utils.pdf_utils import image_bytes_to_pil
    jpeg_bytes = _make_blank_jpeg_bytes()
    img = image_bytes_to_pil(jpeg_bytes)
    assert img.size == (200, 200)
    print("[PASS] test_image_bytes_to_pil")


def test_gemini_json_parser_clean():
    """parse_llm_json should handle clean JSON."""
    from document_agent.utils.groq_utils import parse_llm_json
    raw = '{"application_number": "1234567890123456", "nin": "123-456-789-0", "first_name": "Manoj", "last_name": "Niraula", "dob_ad": "1995-04-12"}'
    result = parse_llm_json(raw)
    assert result["first_name"] == "Manoj"
    assert result["nin"] == "123-456-789-0"
    print("[PASS] test_gemini_json_parser_clean")


def test_gemini_json_parser_with_fences():
    """parse_llm_json should strip markdown code fences."""
    from document_agent.utils.groq_utils import parse_llm_json
    raw = '```json\n{"application_number": null, "nin": null, "first_name": null, "last_name": null, "dob_ad": null}\n```'
    result = parse_llm_json(raw)
    assert result["application_number"] is None
    print("[PASS] test_gemini_json_parser_with_fences")


def test_blur_check_blurry_image():
    """
    A uniform white JPEG has no edges → Laplacian variance = 0 → blurry verdict.
    Does NOT require Gemini key (stops at quality gate).
    """
    from document_agent.pipeline import run_pipeline
    jpeg_bytes = _make_blank_jpeg_bytes()
    result     = run_pipeline("NIN", jpeg_bytes, file_type="image")
    report     = result.get("report", {})
    assert report["verdict"] == "blurry", f"Expected blurry, got: {report['verdict']}"
    assert report["status"]  == "rejected"
    print("[PASS] test_blur_check_blurry_image")
    print("       Report:", json.dumps(report, indent=2, ensure_ascii=False))


def test_normalise_fields():
    """_normalise_fields should fill missing keys with None."""
    from document_agent.agents.extraction_agent import _normalise_fields
    partial = {"application_number": "1234567890123456", "nin": "123-456-789-0"}
    result  = _normalise_fields(partial)
    assert result["first_name"] is None
    assert result["last_name"]  is None
    assert result["dob_ad"]     is None
    assert result["application_number"] == "1234567890123456"
    print("[PASS] test_normalise_fields")


def test_extraction_agent_empty_ocr():
    """extract_fields with empty ocr_text should return null fields and an error."""
    from document_agent.agents.extraction_agent import extract_fields
    from document_agent.utils.state import DocumentState

    state: DocumentState = {
        "image_path": "", "file_bytes": b"", "file_type": "image",
        "image_array": None, "gray_array": None,
        "laplacian_variance": 0.0, "fft_energy": 0.0,
        "regional_scores": [], "blur_score": 0.0,
        "verdict": "clear", "confidence": 0.9, "reason": "",
        "reupload_message": "", "ocr_text": "", "ocr_error": "",
        "extracted_fields": {}, "extraction_error": "", "report": {},
    }
    result = extract_fields(state)
    assert result["extracted_fields"]["application_number"] is None
    assert "No OCR text" in result["extraction_error"]
    print("[PASS] test_extraction_agent_empty_ocr")


# ── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_state_imports,
        test_prompt_content,
        test_merge_ocr_passes,
        test_image_bytes_to_pil,
        test_gemini_json_parser_clean,
        test_gemini_json_parser_with_fences,
        test_normalise_fields,
        test_extraction_agent_empty_ocr,
        test_blur_check_blurry_image,      # needs cv2 + pytesseract installed
    ]

    passed = failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {test.__name__}: {exc}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
