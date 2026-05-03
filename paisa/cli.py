from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

from . import __version__
from . import telemetry as telemetry_module

# Paisa hosted API endpoint
PAISA_API_URL = "https://paisa-api.vercel.app/route"


def _ensure_telemetry_db() -> None:
    data_dir = Path.home() / ".paisa"
    data_dir.mkdir(parents=True, exist_ok=True)
    telemetry_module._DB_PATH = str(data_dir / "telemetry.db")
    telemetry_module._init_db()


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

    try:
        response = requests.post(
            PAISA_API_URL,
            json={"prompt": prompt},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        print("Error: Paisa server unreachable. Try again later.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Error: Paisa server timeout. Try again later.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            error_detail = response.json().get("detail", {})
            if isinstance(error_detail, dict) and "error" in error_detail:
                print(f"Error: {error_detail['error']}")
            else:
                print("Error: Daily limit reached. Come back tomorrow.")
        else:
            error_detail = response.json().get("detail", {})
            if isinstance(error_detail, dict) and "error" in error_detail:
                print(f"Error: {error_detail['error']}")
            else:
                print(f"Error: {str(e)}")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error: Invalid server response - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    if args.json:
        output = {
            "prompt": prompt,
            "label": data.get("label"),
            "confidence": data.get("confidence"),
            "model_used": data.get("model_used"),
            "latency_ms": data.get("latency_ms"),
            "toon_tokens": data.get("toon_tokens"),
            "json_tokens": data.get("json_tokens"),
            "tokens_saved_percent": (
                (1 - (data.get("toon_tokens", 0) / data.get("json_tokens", 1))) * 100
                if data.get("json_tokens")
                else 0
            ),
            "tier_blurred": data.get("tier_blurred", False),
            "fallback_used": data.get("fallback_used", False),
            "response": data.get("response"),
        }
        print(json.dumps(output, indent=2))
        return

    _render_output(
        prompt=prompt,
        label=data.get("label", "UNKNOWN"),
        confidence=data.get("confidence", 0),
        model_used=data.get("model_used", "unknown"),
        latency_ms=data.get("latency_ms", 0),
        toon_tokens=data.get("toon_tokens", 0),
        json_tokens=data.get("json_tokens", 0),
        tier_blurred=data.get("tier_blurred", False),
        response=data.get("response", "No response"),
    )


if __name__ == "__main__":
    main()
