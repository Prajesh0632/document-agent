"""
extraction_agent.py
-------------------
LangGraph node: sends OCR text to Gemini Flash and parses the JSON response.

Input  (from DocumentState): ocr_text
Output (to DocumentState)  : extracted_fields (dict), extraction_error
"""

from __future__ import annotations
import logging

from document_agent.utils.state import DocumentState
from document_agent.utils.groq_utils import call_llm, parse_llm_json

logger = logging.getLogger(__name__)


def extract_fields(state: DocumentState) -> DocumentState:
    """
    LangGraph node — sends merged OCR text to Gemini Flash using the
    NIN extraction prompt, then parses and validates the JSON response.

    On success  : extracted_fields contains the five structured fields.
    On failure  : extraction_error contains the error message,
                  extracted_fields is an empty dict with null values.
    """
    ocr_text: str = state.get("ocr_text", "").strip()

    if not ocr_text:
        logger.warning("extract_fields called with empty ocr_text.")
        return {
            **state,
            "extracted_fields": _null_fields(),
            "extraction_error": "No OCR text available — cannot extract fields.",
        }

    try:
        logger.info("Calling Gemini Flash for field extraction...")
        raw_response = call_llm(state["extraction_prompt"], ocr_text)
        fields       = parse_llm_json(raw_response)

        # Ensure all expected keys are present (fill missing ones with None)
        fields = _normalise_fields(fields)

        logger.info("Extraction successful: %s", fields)
        return {
            **state,
            "extracted_fields": fields,
            "extraction_error": "",
        }

    except Exception as exc:
        logger.error("Extraction failed: %s", exc, exc_info=True)
        return {
            **state,
            "extracted_fields": _null_fields(),
            "extraction_error": str(exc),
        }


def _null_fields() -> dict:
    return {
        "application_number": None,
        "nin":                None,
        "first_name":         None,
        "last_name":          None,
        "dob_ad":             None,
    }


def _normalise_fields(raw: dict) -> dict:
    """
    Ensure every expected key is present.
    Extra keys returned by Gemini are silently dropped.
    """
    expected = _null_fields()
    for key in expected:
        expected[key] = raw.get(key)
    return expected
