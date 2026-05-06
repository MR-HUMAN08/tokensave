from __future__ import annotations

from typing import Dict, List, Tuple

PROVIDER_MODELS = {
    "GROQ_API_KEY": {
        "SIMPLE": "groq/llama-3.1-8b-instant",
        "MODERATE": "groq/llama-3.3-70b-versatile",
        "COMPLEX": "groq/llama-3.3-70b-versatile",
    },
    "GOOGLE_API_KEY": {
        "SIMPLE": "gemini/gemini-2.0-flash",
        "MODERATE": "gemini/gemini-2.0-flash",
        "COMPLEX": "gemini/gemini-2.0-flash",
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
    "HF_TOKEN": {
        "SIMPLE": "huggingface/mistralai/Mistral-7B-Instruct-v0.3",
        "MODERATE": "huggingface/mistralai/Mistral-7B-Instruct-v0.3",
        "COMPLEX": "huggingface/mistralai/Mistral-7B-Instruct-v0.3",
    },
}

PROVIDER_PRIORITY = [
    "GROQ_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "HF_TOKEN",
]

health_scores: Dict[str, Dict[str, float]] = {}


def get_available_providers(keys: Dict[str, str]) -> List[str]:
    return [p for p in PROVIDER_PRIORITY if p in keys and keys[p]]


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


def get_best_model(label: str, keys: Dict[str, str] | None = None) -> Tuple[str, str]:
    """
    Returns (model_string, provider_key_name)
    Only picks models for which user has a key.
    """
    if keys is None:
        from .cli import _load_keys

        keys = _load_keys()

    available = get_available_providers(keys)

    if not available:
        raise ValueError("No API keys found. Run: paisa keys --add")

    for provider in available:
        if provider in PROVIDER_MODELS:
            model = PROVIDER_MODELS[provider][label]
            return model, provider

    raise ValueError("No suitable model found for available keys.")
