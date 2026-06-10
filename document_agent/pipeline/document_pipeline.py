"""
document_pipeline.py
--------------------
Top-level LangGraph pipeline that wires together:

  1. Image quality gate  (intake_agent nodes: load → preprocess → blur check)
  2. OCR node            (ocr_agent:   pytesseract dual-pass)
  3. Extraction node     (extraction_agent: Gemini Flash)
  4. Report node         (generate_report)

Usage (from function_app.py or tests):

    from document_agent.pipeline import run_pipeline

    result = run_pipeline("NIN", file_bytes=b"...", file_type="pdf")
    print(result["report"])
"""

from __future__ import annotations
import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from document_agent.utils.state import DocumentState
from document_agent.prompts import prompts
from document_agent.utils.node import (
    load_image,
    preprocess_image,
    analyze_blur,
    flag_blur,
    mark_ok,
    deep_check,
    ask_reupload,
    generate_report,
    route_decision,
)
from document_agent.agents.ocr_agent import run_ocr
from document_agent.agents.extraction_agent import extract_fields

logger = logging.getLogger(__name__)


# ── Routing functions ────────────────────────────────────────────────────────

def route_after_quality(
    state: DocumentState,
) -> Literal["run_ocr", "ask_reupload"]:
    """
    Called after flag_blur and deep_check.
    Blurry images are rejected; everything else proceeds to OCR.
    """
    if state.get("verdict") == "blurry":
        return "ask_reupload"
    return "run_ocr"


def route_after_ocr(
    state: DocumentState,
) -> Literal["extract_fields", "generate_report"]:
    """
    If OCR produced usable text, proceed to Gemini extraction.
    If OCR failed or returned empty text, skip extraction and report the error.
    """
    if state.get("ocr_error") or not state.get("ocr_text", "").strip():
        logger.warning("OCR produced no text — skipping extraction.")
        return "generate_report"
    return "extract_fields"


# ── Graph builder ────────────────────────────────────────────────────────────

def build_nin_graph():
    graph = StateGraph(DocumentState)

    # ── Blur-check nodes (reuse existing, unchanged) ─────────────────────
    graph.add_node("load_image",       load_image)
    graph.add_node("preprocess_image", preprocess_image)
    graph.add_node("analyze_blur",     analyze_blur)
    graph.add_node("flag_blur",        flag_blur)
    graph.add_node("mark_ok",          mark_ok)
    graph.add_node("deep_check",       deep_check)
    graph.add_node("ask_reupload",     ask_reupload)

    # ── New nodes ────────────────────────────────────────────────────────
    graph.add_node("run_ocr",          run_ocr)
    graph.add_node("extract_fields",  extract_fields)
    graph.add_node("generate_report",  generate_report)

    # ── Edges: quality gate ──────────────────────────────────────────────
    graph.set_entry_point("load_image")
    graph.add_edge("load_image",       "preprocess_image")
    graph.add_edge("preprocess_image", "analyze_blur")

    graph.add_conditional_edges(
        "analyze_blur",
        route_decision,
        {
            "blurry":     "flag_blur",
            "borderline": "deep_check",
            "clear":      "mark_ok",
        },
    )

    # flag_blur and deep_check both route through route_after_quality
    graph.add_conditional_edges(
        "flag_blur",
        route_after_quality,
        {"ask_reupload": "ask_reupload", "run_ocr": "run_ocr"},
    )
    graph.add_conditional_edges(
        "deep_check",
        route_after_quality,
        {"ask_reupload": "ask_reupload", "run_ocr": "run_ocr"},
    )

    # clear images go straight to OCR
    graph.add_edge("mark_ok", "run_ocr")

    # ── Edges: OCR → extraction → report ────────────────────────────────
    graph.add_conditional_edges(
        "run_ocr",
        route_after_ocr,
        {"extract_fields": "extract_fields", "generate_report": "generate_report"},
    )
    graph.add_edge("extract_fields",  "generate_report")

    # rejection path also ends at generate_report
    graph.add_edge("ask_reupload",    "generate_report")

    graph.add_edge("generate_report", END)

    return graph.compile()


# ── Public entry point ───────────────────────────────────────────────────────

def run_pipeline(document: str, file_bytes: bytes, file_type: str = "image") -> dict:
    """
    Run the full NIN extraction pipeline.

    Parameters
    ----------
    file_bytes : raw bytes of the uploaded PDF or image
    file_type  : "pdf" or "image"

    Returns
    -------
    Final DocumentState dict. Access result["report"] for the structured output.
    """
    agent = build_nin_graph()

    initial_state: DocumentState = {
        # Input
        "image_path":         "",
        "file_bytes":         file_bytes,
        "file_type":          file_type,
        # Blur-check
        "image_array":        None,
        "gray_array":         None,
        "laplacian_variance": 0.0,
        "fft_energy":         0.0,
        "regional_scores":    [],
        "blur_score":         0.0,
        "verdict":            "",
        "confidence":         0.0,
        "reason":             "",
        "reupload_message":   "",
        # OCR
        "ocr_text":           "",
        "ocr_error":          "",
        # Extraction
        "extraction_prompt": prompts[f"{document}_EXTRACTION_PROMPT"],
        "extracted_fields":   {},
        "extraction_error":   "",
        # Report
        "report":             {},
    }

    logger.info("Starting NIN pipeline. file_type=%s, bytes=%d", file_type, len(file_bytes))
    final_state = agent.invoke(initial_state)
    logger.info("Pipeline complete. status=%s", final_state.get("report", {}).get("status"))
    return final_state
