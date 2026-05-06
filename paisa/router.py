from __future__ import annotations

import sqlite3
from typing import Dict, List, Tuple

PROVIDER_MODELS = {
    "GROQ_API_KEY": {
        "SIMPLE": "groq/llama-3.1-8b-instant",
        "MODERATE": "groq/llama-3.3-70b-versatile",
        "COMPLEX": "groq/llama-3.3-70b-versatile",
    },
    "GOOGLE_API_KEY": {
        "SIMPLE": "gemini/gemini-1.5-flash",
        "MODERATE": "gemini/gemini-1.5-flash",
        "COMPLEX": "gemini/gemini-1.5-flash",
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

MODEL_EFFICIENCY = {
    "groq/llama-3.1-8b-instant": 0.95,
    "groq/llama-3.3-70b-versatile": 0.8,
    "gemini/gemini-1.5-flash": 0.9,
    "claude-3-haiku-20240307": 0.85,
    "claude-3-5-sonnet-20241022": 0.7,
    "gpt-4o-mini": 0.85,
    "gpt-4o": 0.6,
    "huggingface/mistralai/Mistral-7B-Instruct-v0.3": 0.75,
}

MODEL_QUALITY = {
    "gpt-4o": 0.95,
    "claude-3-5-sonnet-20241022": 0.93,
    "groq/llama-3.3-70b-versatile": 0.9,
    "gemini/gemini-1.5-flash": 0.75,
    "gpt-4o-mini": 0.7,
    "claude-3-haiku-20240307": 0.68,
    "groq/llama-3.1-8b-instant": 0.65,
    "huggingface/mistralai/Mistral-7B-Instruct-v0.3": 0.6,
}

health_scores: Dict[str, Dict[str, float]] = {}


def get_available_providers(keys: Dict[str, Dict[str, str | None]]) -> List[str]:
    available: List[str] = []
    for provider in PROVIDER_PRIORITY:
        entry = keys.get(provider)
        if isinstance(entry, dict) and entry.get("key"):
            available.append(provider)
    # Include any custom providers not in the priority list
    for provider, entry in keys.items():
        if provider in PROVIDER_PRIORITY:
            continue
        if isinstance(entry, dict) and entry.get("key"):
            available.append(provider)
    return available


def get_provider_for_model(model: str) -> str | None:
    for provider, models in PROVIDER_MODELS.items():
        if model in models.values():
            return provider
    return None


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


def _health_penalty(model: str) -> float:
    stats = health_scores.get(model, {"latency_avg": 0.0, "error_rate": 0.0, "calls": 0.0})
    return stats.get("latency_avg", 0.0) + stats.get("error_rate", 0.0) * 10000


def _avg_toon_tokens(model: str) -> float | None:
    try:
        from . import telemetry as telemetry_module

        db_path = telemetry_module._DB_PATH
    except Exception:
        return None

    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT AVG(toon_token_count) FROM logs WHERE model_used = ?",
                (model,),
            )
            row = cursor.fetchone()
            if row and row[0] is not None:
                return float(row[0])
    except Exception:
        return None
    return None


def get_preferred_model_for_label(label: str, available_keys: Dict[str, Dict[str, str | None]]) -> Tuple[str, str]:
    available = get_available_providers(available_keys)
    if not available:
        raise ValueError("No API keys found. Run: paisa keys --add")

    candidates: List[Tuple[str, str]] = []
    for provider in available:
        if provider in PROVIDER_MODELS:
            model = PROVIDER_MODELS.get(provider, {}).get(label)
        else:
            model = (available_keys.get(provider) or {}).get("model")
        if model:
            candidates.append((provider, model))

    if not candidates:
        raise ValueError("No suitable model found for available keys.")

    if label == "SIMPLE":
        best_provider, best_model = max(
            candidates,
            key=lambda item: (
                MODEL_EFFICIENCY.get(item[1], 0.0),
                -_health_penalty(item[1]),
                -(_avg_toon_tokens(item[1]) or 0.0),
            ),
        )
        return best_model, best_provider

    if label == "MODERATE":
        filtered = [item for item in candidates if MODEL_EFFICIENCY.get(item[1], 0.0) > 0.7]
        pool = filtered or candidates
        best_provider, best_model = max(
            pool,
            key=lambda item: (
                MODEL_EFFICIENCY.get(item[1], 0.0),
                -_health_penalty(item[1]),
                -(_avg_toon_tokens(item[1]) or 0.0),
            ),
        )
        return best_model, best_provider

    best_provider, best_model = max(
        candidates,
        key=lambda item: (
            MODEL_QUALITY.get(item[1], 0.0),
            -_health_penalty(item[1]),
            -(_avg_toon_tokens(item[1]) or 0.0),
        ),
    )
    return best_model, best_provider


def get_best_model_for_keys(label: str, keys_dict: Dict[str, Dict[str, str | None]]) -> Tuple[str, str]:
    available = get_available_providers(keys_dict)
    if not available:
        raise ValueError("No API keys found. Run: paisa keys --add")

    if len(available) == 1:
        provider = available[0]
        if provider in PROVIDER_MODELS:
            model = PROVIDER_MODELS.get(provider, {}).get(label)
        else:
            model = (keys_dict.get(provider) or {}).get("model")
        if not model:
            raise ValueError("No suitable model found for available keys.")
        return model, provider

    return get_preferred_model_for_label(label, keys_dict)


def get_best_model(label: str, keys: Dict[str, Dict[str, str | None]] | None = None) -> Tuple[str, str]:
    if keys is None:
        from .cli import _load_keys

        keys = _load_keys()

    return get_best_model_for_keys(label, keys)
