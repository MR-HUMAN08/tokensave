from __future__ import annotations

from typing import Dict

SIMPLE_MODEL = "groq/llama-3.1-8b-instant"
MODERATE_MODEL = "groq/llama-3.3-70b-versatile"
COMPLEX_MODEL = "groq/llama-3.3-70b-versatile"
FALLBACK_MODEL = "gemini/gemini-1.5-flash"

health_scores: Dict[str, Dict[str, float]] = {
    SIMPLE_MODEL: {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0},
    MODERATE_MODEL: {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0},
    COMPLEX_MODEL: {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0},
    FALLBACK_MODEL: {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0},
}


def get_model(label: str) -> str:
    if label == "SIMPLE":
        return SIMPLE_MODEL
    if label == "MODERATE":
        return MODERATE_MODEL
    if label == "COMPLEX":
        return COMPLEX_MODEL
    return FALLBACK_MODEL


def update_health(model: str, latency_ms: float, error: bool = False) -> Dict[str, float]:
    stats = health_scores.setdefault(
        model, {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0}
    )

    calls = stats["calls"]
    stats["latency_avg"] = (stats["latency_avg"] * calls + latency_ms) / (calls + 1)
    stats["calls"] = calls + 1

    if error:
        errors = stats["error_rate"] * calls + 1
        stats["error_rate"] = errors / stats["calls"]
    else:
        errors = stats["error_rate"] * calls
        stats["error_rate"] = errors / stats["calls"]

    return stats


def get_best_model(label: str) -> str:
    if label == "SIMPLE":
        candidates = [SIMPLE_MODEL]
    elif label == "MODERATE":
        candidates = [MODERATE_MODEL]
    elif label == "COMPLEX":
        candidates = [COMPLEX_MODEL]
    else:
        candidates = [FALLBACK_MODEL]

    best_model = candidates[0]
    best_score = float("inf")
    for model in candidates:
        stats = health_scores.get(model, {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0})
        calls = stats.get("calls", 0.0)
        if calls == 0:
            score = 0.0
        else:
            score = stats.get("latency_avg", 0.0) + stats.get("error_rate", 0.0) * 10000

        if score < best_score:
            best_score = score
            best_model = model

    return best_model
