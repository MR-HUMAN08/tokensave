from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, List

import litellm

from .router import PROVIDER_MODELS, get_available_providers, update_health

if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

PROVIDER_ENV_VAR = {
    "GROQ_API_KEY": "GROQ_API_KEY",
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY": "OPENAI_API_KEY",
    "GOOGLE_API_KEY": "GOOGLE_API_KEY",
    "HF_TOKEN": "HF_TOKEN",
}


def _model_to_provider(model: str) -> str | None:
    for provider, models in PROVIDER_MODELS.items():
        if model in models.values():
            return provider
    return None


def _model_to_label(model: str) -> str | None:
    for provider, models in PROVIDER_MODELS.items():
        for label, value in models.items():
            if value == model:
                return label
    return None


def call_with_fallback(
    prompt: str,
    original_model: str,
    keys: Dict[str, Dict[str, str | None]] | None = None,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    if keys is None:
        from .cli import _load_keys

        keys = _load_keys()

    available_providers = get_available_providers(keys)
    target_label = _model_to_label(original_model) or "SIMPLE"

    fallback_models: List[str] = []
    for provider in available_providers:
        if provider in PROVIDER_MODELS:
            candidate = PROVIDER_MODELS[provider].get(target_label)
        else:
            candidate = (keys.get(provider) or {}).get("model")
        if candidate and candidate != original_model:
            fallback_models.append(candidate)

    models_to_try = [original_model] + fallback_models
    seen = set()
    deduped_models: List[str] = []
    for m in models_to_try:
        if m not in seen:
            seen.add(m)
            deduped_models.append(m)

    for attempt_model in deduped_models:
        provider = _model_to_provider(attempt_model)
        if provider is None:
            for name, entry in keys.items():
                if (entry or {}).get("model") == attempt_model:
                    provider = name
                    break
        env_var = PROVIDER_ENV_VAR.get(provider, provider or "")
        prev_value = os.environ.get(env_var) if env_var else None
        if env_var and provider in keys:
            key_value = (keys.get(provider) or {}).get("key")
            if key_value:
                os.environ[env_var] = key_value

        start = time.time()
        try:
            # Build messages with history for context
            if history:
                messages = history + [{"role": "user", "content": prompt}]
            else:
                messages = [{"role": "user", "content": prompt}]

            response = litellm.completion(
                model=attempt_model,
                messages=messages,
            )
            latency_ms = (time.time() - start) * 1000
            update_health(attempt_model, latency_ms, error=False)
            return {
                "response": response.choices[0].message.content,
                "model_used": attempt_model,
                "latency_ms": latency_ms,
                "success": True,
                "fallback_used": attempt_model != original_model,
            }
        except Exception:
            update_health(attempt_model, (time.time() - start) * 1000, error=True)
            print(f"[fallback] Model {attempt_model} failed, trying next...")
        finally:
            if env_var:
                if prev_value is None:
                    os.environ.pop(env_var, None)
                else:
                    os.environ[env_var] = prev_value

    return {
        "response": "All models failed. Check your API keys with: paisa keys --list",
        "model_used": original_model,
        "latency_ms": 0,
        "success": False,
        "fallback_used": False,
    }
