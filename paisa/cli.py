from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from . import __version__
from . import telemetry as telemetry_module


def _ensure_telemetry_db() -> None:
    data_dir = Path.home() / ".paisa"
    data_dir.mkdir(parents=True, exist_ok=True)
    telemetry_module._DB_PATH = str(data_dir / "telemetry.db")
    telemetry_module._init_db()


def _print_setup_message() -> None:
    print(
        "No API keys found. Create a .env file with:\n"
        "GROQ_API_KEY=your_key\n"
        "GOOGLE_API_KEY=your_key\n"
        "Then run tokenwise again."
    )


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


def _get_model_label(label: str, confidence: float) -> tuple[str, bool]:
    if label == "COMPLEX" and confidence < 0.75:
        return "MODERATE", True
    if label == "MODERATE" and confidence < 0.65:
        return "SIMPLE", True
    return label, False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Paisa CLI - Smart LLM routing that saves you money"
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to route")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--stats", action="store_true", help="Show telemetry stats")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args()

    load_dotenv()
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

    if not os.getenv("GROQ_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        _print_setup_message()
        sys.exit(1)

    from .classifier import classify
    from .fallback import call_with_fallback
    from .router import get_best_model
    from .toon_layer import count_tokens, to_toon

    label, confidence = classify(prompt)
    model_label, tier_blurred = _get_model_label(label, confidence)
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
