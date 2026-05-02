from __future__ import annotations

from typing import Dict

SIMPLE_MODEL = "groq/llama-3.1-8b-instant"
MODERATE_MODEL = "groq/llama-3.3-70b-versatile"
COMPLEX_MODEL = "groq/llama-3.3-70b-versatile"
FALLBACK_MODEL = "gemini/gemini-1.5-flash"

health_scores: Dict[str, float] = {
    SIMPLE_MODEL: 1.0,
    MODERATE_MODEL: 1.0,
    COMPLEX_MODEL: 1.0,
    FALLBACK_MODEL: 1.0,
}


def get_model(label: str) -> str:
    if label == "SIMPLE":
        return SIMPLE_MODEL
    if label == "MODERATE":
        return MODERATE_MODEL
    if label == "COMPLEX":
        return COMPLEX_MODEL
    return FALLBACK_MODEL


def update_health(model: str, latency_ms: float, error: bool = False) -> float:
    previous = health_scores.get(model, 1.0)
    if error:
        updated = max(0.0, previous * 0.7)
    else:
        latency_score = 1.0 / (1.0 + max(latency_ms, 0.0) / 1000.0)
        updated = 0.8 * previous + 0.2 * latency_score

    health_scores[model] = updated
    return updated
