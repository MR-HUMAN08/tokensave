from __future__ import annotations

import os
from typing import Dict, List

FALLBACK_MODEL = "groq/llama-3.1-8b-instant"

PROVIDER_MODELS = {
    "GROQ_API_KEY": {
        "SIMPLE": "groq/llama-3.1-8b-instant",
        "MODERATE": "groq/llama-3.3-70b-versatile",
        "COMPLEX": "groq/llama-3.3-70b-versatile",
    },
    "ANTHROPIC_API_KEY": {
        "SIMPLE": "claude-3-haiku-20240307",
        "MODERATE": "claude-3-5-sonnet-20241022",
        "COMPLEX": "claude-3-5-sonnet-20241022",
    },
    "OPENAI_API_KEY": {
        "SIMPLE": "gpt-4o-mini",
        "MODERATE": "gpt-4o",
        "COMPLEX": "gpt-4o",
    },
    "GOOGLE_API_KEY": {
        "SIMPLE": "gemini/gemini-2.0-flash",
        "MODERATE": "gemini/gemini-2.0-flash",
        "COMPLEX": "gemini/gemini-2.0-flash",
    },
}

TIER_PRIORITY = {
    "SIMPLE": ["GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"],
    "MODERATE": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY"],
    "COMPLEX": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY"],
}

health_scores: Dict[str, Dict[str, float]] = {}


def _has_key(key_name: str) -> bool:
    return bool(os.environ.get(key_name))


def _build_candidates(label: str) -> List[str]:
    candidates: List[str] = []
    for key_name in TIER_PRIORITY.get(label, []):
        if _has_key(key_name):
            model = PROVIDER_MODELS[key_name][label]
            candidates.append(model)
    return candidates


def get_model(label: str) -> str:
    candidates = _build_candidates(label)
    if candidates:
        return candidates[0]
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
    if label in {"SIMPLE", "MODERATE", "COMPLEX"}:
        candidates = _build_candidates(label)
    else:
        candidates = []

    if not candidates:
        candidates = [FALLBACK_MODEL]

    best_model = candidates[0]
    best_score = float("inf")
    for model in candidates:
        stats = health_scores.setdefault(
            model, {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0}
        )
        calls = stats.get("calls", 0.0)
        if calls == 0:
            score = 0.0
        else:
            score = stats.get("latency_avg", 0.0) + stats.get("error_rate", 0.0) * 10000

        if score < best_score:
            best_score = score
            best_model = model

    return best_model
