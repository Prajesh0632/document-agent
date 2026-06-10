from document_agent.utils.state import DocumentState
from typing import Literal
from dotenv import load_dotenv
import os
import cv2
import numpy as np

load_dotenv(".env.local")

## Threshold values
LAP_THRESHOLD_LOW  = 50
LAP_THRESHOLD_HIGH = 200
FFT_THRESHOLD_LOW  = 0.03
FFT_THRESHOLD_HIGH = 0.12


def load_image(state: DocumentState) -> DocumentState:
    """
    Load image into state.
    - If file_type is 'pdf': convert first page to numpy array via pdf_utils
    - If file_type is 'image': decode bytes directly with cv2
    - Falls back to file path mode for standalone blur testing
    """
    file_bytes = state.get("file_bytes", b"")
    file_type  = state.get("file_type", "image")

    # ── PDF mode: convert first page → numpy array ────────────────────
    if file_type == "pdf" and file_bytes:
        try:
            from document_agent.utils.pdf_utils import pdf_bytes_to_images
            pages = pdf_bytes_to_images(file_bytes, dpi=300)
            if not pages:
                raise ValueError("PDF conversion produced no pages.")
            pil_page = pages[0]
            import numpy as np
            img = cv2.cvtColor(np.array(pil_page.convert("RGB")), cv2.COLOR_RGB2BGR)
            return {**state, "image_array": img, "image_path": "pdf_page_1"}
        except Exception as exc:
            raise ValueError(f"Could not convert PDF to image: {exc}") from exc

    # ── Image bytes mode ──────────────────────────────────────────────
    if file_bytes and file_type == "image":
        import numpy as np
        arr = np.frombuffer(file_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes.")
        return {**state, "image_array": img, "image_path": "uploaded_image"}

    # ── File path mode (standalone testing) ───────────────────────────
    path = state.get("image_path", "")
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Could not decode image: {path}")
    return {**state, "image_array": img}


def preprocess_image(state: DocumentState) -> DocumentState:
    img  = state["image_array"]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    h, w = gray.shape
    if max(h, w) > 1024:
        scale = 1024 / max(h, w)
        gray  = cv2.resize(gray, (int(w * scale), int(h * scale)),
                           interpolation=cv2.INTER_AREA)
    return {**state, "gray_array": gray}


def analyze_blur(state: DocumentState) -> DocumentState:
    gray    = state["gray_array"]
    lap     = cv2.Laplacian(gray, cv2.CV_64F)
    lap_var = lap.var()

    min_val, max_val, _, _ = cv2.minMaxLoc(gray)
    contrast_range = max_val - min_val + 1e-9
    scaled_lap_var = lap_var / contrast_range

    f      = np.fft.fft2(gray.astype(np.float32))
    fshift = np.fft.fftshift(f)
    mag    = np.abs(fshift)
    h, w   = mag.shape
    cy, cx = h // 2, w // 2
    r      = min(h, w) // 10
    mask   = np.ones((h, w), dtype=bool)
    mask[cy - r:cy + r, cx - r:cx + r] = False
    total      = mag.sum() + 1e-9
    fft_energy = mag[mask].sum() / total

    lap_norm   = min(scaled_lap_var / 2.0, 1.0)
    fft_norm   = min(fft_energy / 0.2, 1.0)
    blur_score = 0.6 * lap_norm + 0.4 * fft_norm

    return {
        **state,
        "laplacian_variance": float(lap_var),
        "fft_energy":         float(fft_energy),
        "blur_score":         float(blur_score),
    }


def route_decision(state: DocumentState) -> Literal["blurry", "borderline", "clear"]:
    score = state["blur_score"]
    if score < 0.30:   return "blurry"
    elif score < 0.72: return "borderline"
    else:              return "clear"


def flag_blur(state: DocumentState) -> DocumentState:
    return {
        **state,
        "verdict":    "blurry",
        "confidence": round(1 - state["blur_score"], 2),
        "reason": (
            f"Laplacian variance {state['laplacian_variance']:.1f} is below "
            f"threshold {LAP_THRESHOLD_LOW}; FFT high-freq energy "
            f"{state['fft_energy']:.4f} is very low."
        ),
    }


def mark_ok(state: DocumentState) -> DocumentState:
    return {
        **state,
        "verdict":    "clear",
        "confidence": round(state["blur_score"], 2),
        "reason": (
            f"Laplacian variance {state['laplacian_variance']:.1f} is above "
            f"threshold {LAP_THRESHOLD_HIGH}; strong high-frequency content detected."
        ),
    }


def deep_check(state: DocumentState) -> DocumentState:
    gray   = state["gray_array"]
    h, w   = gray.shape
    rh, rw = h // 3, w // 3
    scores = []
    for r in range(3):
        for c in range(3):
            patch = gray[r*rh:(r+1)*rh, c*rw:(c+1)*rw]
            lap   = cv2.Laplacian(patch, cv2.CV_64F)
            scores.append(float(lap.var()))

    sharp_regions  = sum(1 for s in scores if s > LAP_THRESHOLD_LOW)
    regional_score = sharp_regions / 9
    combined       = 0.5 * state["blur_score"] + 0.5 * regional_score

    if combined < 0.30:   verdict, conf = "blurry",     round(1 - combined, 2)
    elif combined < 0.72: verdict, conf = "borderline", round(0.5, 2)
    else:                 verdict, conf = "clear",      round(combined, 2)

    return {
        **state,
        "regional_scores": scores,
        "verdict":         verdict,
        "confidence":      conf,
        "reason": (
            f"{sharp_regions}/9 regions are sharp "
            f"(Laplacian > {LAP_THRESHOLD_LOW}). "
            f"Combined score: {combined:.2f}."
        ),
    }


def route_after_verdict(
    state: DocumentState,
) -> Literal["ask_reupload", "generate_report"]:
    if state["verdict"] == "blurry":
        return "ask_reupload"
    return "generate_report"


def ask_reupload(state: DocumentState) -> DocumentState:
    message = (
        "Image is not suitable for field extraction.\n\n"
        f"Reason:\n  - {state['reason']}\n\n"
        "Please reupload a better image:\n"
        "  - Hold the camera steady (avoid camera shake)\n"
        "  - Ensure the document is well lit\n"
        "  - Avoid shadows, glare, or obstructions\n"
        "  - Place the document flat before capturing"
    )
    return {**state, "reupload_message": message}


def generate_report(state: DocumentState) -> DocumentState:
    base = {
        "image":      state.get("image_path", ""),
        "verdict":    state.get("verdict", ""),
        "confidence": state.get("confidence", 0.0),
        "blur_score": round(state.get("blur_score", 0.0), 4),
        "reason":     state.get("reason", ""),
    }

    if state.get("verdict") == "blurry":
        report = {
            **base,
            "status":           "rejected",
            "reupload_message": state.get("reupload_message", ""),
        }
    else:
        report = {
            **base,
            "status":            "success",
            "extracted_fields":  state.get("extracted_fields", {}),
            "extraction_error":  state.get("extraction_error", ""),
        }

    if state.get("regional_scores"):
        report["regional_sharpness"] = [round(s, 1) for s in state["regional_scores"]]

    return {**state, "report": report}
