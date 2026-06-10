from __future__ import annotations
import json
import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv(".env.local")

logger = logging.getLogger(__name__)

_MODEL_NAME = "llama-3.3-70b-versatile"
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com/keys"
            )
        _client = Groq(api_key=api_key)
        logger.info("Groq client initialised with model: %s", _MODEL_NAME)
    return _client


def call_llm(prompt: str, ocr_text: str) -> str:
    client      = _get_client()
    full_prompt = f"{prompt}\n\n### OCR Text:\n{ocr_text}"

    response = client.chat.completions.create(
        model=_MODEL_NAME,
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.0,
        max_tokens=512,
    )
    raw = response.choices[0].message.content.strip()
    logger.debug("Groq raw response: %s", raw[:200])
    return raw


def parse_llm_json(raw_response: str) -> dict:
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines   = cleaned.splitlines()
        cleaned = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned non-JSON output: {raw_response!r}"
        ) from exc