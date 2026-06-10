"""
intake_agent.py
---------------
Standalone LangGraph blur-detection agent.
Used directly for testing image quality in isolation.
The full document pipeline reuses all these nodes
but wires them into the larger extraction graph.
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END
from document_agent.utils.state import DocumentState
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
    route_after_verdict,
)


def build_graph():
    """Build and compile the standalone blur-check graph."""
    graph = StateGraph(DocumentState)

    graph.add_node("load_image",       load_image)
    graph.add_node("preprocess_image", preprocess_image)
    graph.add_node("analyze_blur",     analyze_blur)
    graph.add_node("flag_blur",        flag_blur)
    graph.add_node("mark_ok",          mark_ok)
    graph.add_node("deep_check",       deep_check)
    graph.add_node("ask_reupload",     ask_reupload)
    graph.add_node("generate_report",  generate_report)

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
    graph.add_conditional_edges(
        "flag_blur",
        route_after_verdict,
        {"ask_reupload": "ask_reupload", "generate_report": "generate_report"},
    )
    graph.add_conditional_edges(
        "deep_check",
        route_after_verdict,
        {"ask_reupload": "ask_reupload", "generate_report": "generate_report"},
    )
    graph.add_edge("mark_ok",          "generate_report")
    graph.add_edge("ask_reupload",     "generate_report")
    graph.add_edge("generate_report",  END)

    return graph.compile()


def check_image_blur(image_path: str) -> dict:
    """
    Convenience function — run blur check on a single image file path.

    Parameters
    ----------
    image_path : absolute or relative path to a JPEG / PNG image

    Returns
    -------
    report dict from the final state
    """
    agent = build_graph()
    initial_state: DocumentState = {
        "image_path":         image_path,
        "file_bytes":         b"",
        "file_type":          "image",
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
        "ocr_text":           "",
        "ocr_error":          "",
        "extracted_fields":   {},
        "extraction_error":   "",
        "report":             {},
    }
    final = agent.invoke(initial_state)
    return final.get("report", {})
