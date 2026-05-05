from __future__ import annotations

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path
from typing import Dict, List, Tuple

from platformdirs import user_config_dir

from . import __version__
from . import telemetry as telemetry_module


KNOWN_KEYS = [
    "GROQ_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "HF_TOKEN",
]

PROVIDER_CHOICES: List[Tuple[str, str]] = [
    ("1", "GROQ_API_KEY"),
    ("2", "GOOGLE_API_KEY"),
    ("3", "ANTHROPIC_API_KEY"),
    ("4", "OPENAI_API_KEY"),
    ("5", "HF_TOKEN"),
    ("6", "Other"),
]


def _ensure_telemetry_db() -> None:
    data_dir = Path.home() / ".paisa"
    data_dir.mkdir(parents=True, exist_ok=True)
    telemetry_module._DB_PATH = str(data_dir / "telemetry.db")
    telemetry_module._init_db()


def _config_path() -> Path:
    config_dir = Path(user_config_dir("paisa", "paisa"))
    return config_dir / "keys.json"


def _load_keys() -> Dict[str, str]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: str(v) for k, v in data.items() if str(v).strip()}


def _save_keys(keys: Dict[str, str]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(keys, indent=2), encoding="utf-8")


def _mask_key(value: str) -> str:
    if len(value) <= 8:
        return f"{value[:4]}...{value[-4:]}" if len(value) > 4 else value
    return f"{value[:4]}...{value[-4:]}"


def _print_welcome() -> None:
    print("┌─────────────────────────────────────┐")
    print("│  Welcome to Paisa!                  │")
    print("└─────────────────────────────────────┘")
    print("Smart LLM routing that saves you money.\n")
    print("No API keys found. Let's set one up.\n")
    print("Supported providers:")
    print("  1. GROQ_API_KEY       (free at console.groq.com)")
    print("  2. GOOGLE_API_KEY     (free at aistudio.google.com)")
    print("  3. ANTHROPIC_API_KEY  (claude.ai/settings)")
    print("  4. OPENAI_API_KEY     (platform.openai.com)")
    print("  5. HF_TOKEN          (huggingface.co/settings/tokens)")
    print("  6. Other             (any LiteLLM-compatible key)")


def _resolve_provider(selection: str) -> str:
    for number, name in PROVIDER_CHOICES:
        if selection == number:
            return name
    return selection


def _prompt_for_first_key() -> Dict[str, str]:
    _print_welcome()

    while True:
        selection = input("Enter provider name (or number): ").strip()
        if not selection:
            print("Provider name is required.")
            continue
        provider = _resolve_provider(selection)
        if provider == "Other":
            provider = input("Enter provider name: ").strip()
            if not provider:
                print("Provider name is required.")
                continue
        key_value = getpass("Enter API key: ").strip()
        if not key_value:
            print("Key value cannot be empty.")
            continue
        keys = {provider: key_value}
        _save_keys(keys)
        path = _config_path()
        print(f"Keys are stored locally in {path}")
        print("They never leave your machine.")
        return keys


def _list_keys() -> None:
    keys = _load_keys()
    if not keys:
        print("No keys stored.")
        return
    for name in sorted(keys.keys()):
        print(f"{name}: {_mask_key(keys[name])}")


def _add_key() -> None:
    keys = _load_keys()
    provider = input(
        "Enter provider name (e.g. GROQ_API_KEY, ANTHROPIC_API_KEY): "
    ).strip()
    if not provider:
        print("Provider name is required.")
        return
    key_value = getpass("Enter key value: ").strip()
    if not key_value:
        print("Key value cannot be empty.")
        return
    keys[provider] = key_value
    _save_keys(keys)
    print(f"Saved {provider}.")


def _remove_key() -> None:
    keys = _load_keys()
    if not keys:
        print("No keys stored.")
        return
    names = sorted(keys.keys())
    for idx, name in enumerate(names, start=1):
        print(f"{idx}. {name}")
    selection = input("Which key to remove? (number): ").strip()
    if not selection.isdigit():
        print("Invalid selection.")
        return
    index = int(selection) - 1
    if index < 0 or index >= len(names):
        print("Invalid selection.")
        return
    removed = names[index]
    keys.pop(removed, None)
    _save_keys(keys)
    print(f"Removed {removed}.")


def _reset_keys() -> None:
    path = _config_path()
    if path.exists():
        path.unlink()
    print("All keys removed. Run paisa to set up again.")


def _ensure_keys_loaded() -> Dict[str, str]:
    keys = _load_keys()
    if not keys:
        keys = _prompt_for_first_key()
    for key, value in keys.items():
        os.environ[key] = value
    return keys


def _render_output(
    prompt: str,
    label: str,
    confidence: float,
    model_used: str,
    latency_ms: float,
    toon_tokens: int,
    json_tokens: int,
    tier_blurred: bool,
    response: str,
) -> None:
    saved = max(json_tokens - toon_tokens, 0)
    percent = 0
    if json_tokens > 0:
        percent = round((saved / json_tokens) * 100)

    print("+-------------------------------------+")
    print("|  Paisa                              |")
    print("+-------------------------------------+")
    print(f"* Prompt    : {prompt}")
    print(f"* Label     : {label} (confidence: {confidence})")
    print(f"* Model     : {model_used}")
    print(f"* Latency   : {int(round(latency_ms))}ms")
    print(f"* Tokens    : TOON {toon_tokens} vs JSON {json_tokens} (saved {percent}%)")
    print(f"* Tier Blur : {'Yes' if tier_blurred else 'No'}")
    print("")
    print("-- Response --------------------------")
    print(response)
    print("--------------------------------------")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "keys":
        keys_parser = argparse.ArgumentParser(
            prog="paisa keys",
            description="Manage locally stored API keys",
        )
        group = keys_parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--list", action="store_true", help="List stored keys")
        group.add_argument("--add", action="store_true", help="Add a new key")
        group.add_argument("--remove", action="store_true", help="Remove a key")
        group.add_argument("--reset", action="store_true", help="Remove all keys")
        keys_args = keys_parser.parse_args(sys.argv[2:])

        if keys_args.list:
            _list_keys()
            return
        if keys_args.add:
            _add_key()
            return
        if keys_args.remove:
            _remove_key()
            return
        if keys_args.reset:
            _reset_keys()
            return

    parser = argparse.ArgumentParser(
        description="Paisa CLI - Smart LLM routing that saves you money"
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to route")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--stats", action="store_true", help="Show telemetry stats")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args()

    _ensure_telemetry_db()

    if args.version:
        print(f"paisa {__version__}")
        return

    if args.stats:
        stats = telemetry_module.get_stats()
        print(json.dumps(stats, indent=2))
        return

    prompt = args.prompt
    if not prompt:
        parser.print_help()
        sys.exit(1)

    _ensure_keys_loaded()

    from .classifier import classify
    from .fallback import call_with_fallback
    from .router import get_best_model
    from .toon_layer import count_tokens, to_toon

    try:
        label, confidence = classify(prompt)
        model_label = label
        tier_blurred = False
        if label == "COMPLEX" and confidence < 0.75:
            model_label = "MODERATE"
            tier_blurred = True
        elif label == "MODERATE" and confidence < 0.65:
            model_label = "SIMPLE"
            tier_blurred = True

        model = get_best_model(model_label)

        toon_payload = to_toon({"prompt": prompt})
        toon_tokens = count_tokens(toon_payload)
        json_payload = json.dumps({"prompt": prompt})
        json_tokens = count_tokens(json_payload)

        result = call_with_fallback(prompt, model)

        telemetry_module.log_request(
            prompt=prompt,
            label=label,
            model_used=result["model_used"],
            latency_ms=result["latency_ms"],
            toon_tokens=toon_tokens,
            json_tokens=json_tokens,
            confidence=confidence,
            tier_blurred=tier_blurred,
            fallback_used=result.get("fallback_used", False),
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.json:
        output = {
            "prompt": prompt,
            "label": label,
            "confidence": confidence,
            "model_used": result["model_used"],
            "latency_ms": result["latency_ms"],
            "toon_tokens": toon_tokens,
            "json_tokens": json_tokens,
            "tokens_saved_percent": (1 - (toon_tokens / json_tokens)) * 100 if json_tokens else 0,
            "tier_blurred": tier_blurred,
            "fallback_used": result.get("fallback_used", False),
            "response": result["response"],
        }
        print(json.dumps(output, indent=2))
        return

    _render_output(
        prompt=prompt,
        label=label,
        confidence=confidence,
        model_used=result["model_used"],
        latency_ms=result["latency_ms"],
        toon_tokens=toon_tokens,
        json_tokens=json_tokens,
        tier_blurred=tier_blurred,
        response=result["response"],
    )


if __name__ == "__main__":
    main()
