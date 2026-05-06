from __future__ import annotations

import time
from typing import Any, Dict

import litellm

from .router import PROVIDER_MODELS, get_available_providers, update_health


def call_with_fallback(prompt: str, model: str, keys: Dict[str, str] | None = None) -> Dict[str, Any]:
    if keys is None:
        from .cli import _load_keys

        keys = _load_keys()

    available_providers = get_available_providers(keys)

    fallback_models = []
    for provider in available_providers:
        candidate = PROVIDER_MODELS[provider].get("SIMPLE")
        if candidate and candidate != model:
            fallback_models.append(candidate)

    models_to_try = [model] + fallback_models

    for attempt_model in models_to_try:
        start = time.time()
        try:
            response = litellm.completion(
                model=attempt_model,
                messages=[{"role": "user", "content": prompt}],
            )
            latency_ms = (time.time() - start) * 1000
            update_health(attempt_model, latency_ms, error=False)
            return {
                "response": response.choices[0].message.content,
                "model_used": attempt_model,
                "latency_ms": latency_ms,
                "success": True,
                "fallback_used": attempt_model != model,
            }
        except Exception:
            update_health(attempt_model, (time.time() - start) * 1000, error=True)
            print(f"[fallback] Model {attempt_model} failed, trying next...")
            continue

    return {
        "response": "All models failed. Check your API keys with: paisa keys --list",
        "model_used": model,
        "latency_ms": 0,
        "success": False,
        "fallback_used": False,
    }
