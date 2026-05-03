from __future__ import annotations

import time
from typing import Any, Dict, Optional

from litellm import completion

from .router import FALLBACK_MODEL, update_health


def _extract_status_code(error: Exception) -> Optional[int]:
    for attr in ("status_code", "status", "http_status"):
        value = getattr(error, attr, None)
        if isinstance(value, int):
            return value
    return None


def _call_model(prompt: str, model: str) -> Dict[str, Any]:
    response = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = ""
    if response and "choices" in response and response["choices"]:
        content = response["choices"][0]["message"]["content"]
    return {"response": content, "model_used": model}


def call_with_fallback(prompt: str, model: str) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        result = _call_model(prompt, model)
        latency_ms = (time.perf_counter() - start) * 1000
        update_health(model, latency_ms, error=False)
        return {
            "response": result["response"],
            "model_used": result["model_used"],
            "latency_ms": latency_ms,
            "success": True,
            "fallback_used": False,
        }
    except Exception as error:  # noqa: BLE001 - surface external API failures
        latency_ms = (time.perf_counter() - start) * 1000
        update_health(model, latency_ms, error=True)
        print(f"[fallback] Model {model} failed, falling back...")

        try:
            fallback_start = time.perf_counter()
            result = _call_model(prompt, FALLBACK_MODEL)
            fallback_latency = (time.perf_counter() - fallback_start) * 1000
            update_health(FALLBACK_MODEL, fallback_latency, error=False)
            return {
                "response": result["response"],
                "model_used": result["model_used"],
                "latency_ms": fallback_latency,
                "success": True,
                "fallback_used": True,
            }
        except Exception as fallback_error:  # noqa: BLE001
            fallback_latency = (time.perf_counter() - start) * 1000
            update_health(FALLBACK_MODEL, fallback_latency, error=True)
            return {
                "response": str(fallback_error),
                "model_used": FALLBACK_MODEL,
                "latency_ms": fallback_latency,
                "success": False,
                "fallback_used": True,
            }
