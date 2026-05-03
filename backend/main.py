from __future__ import annotations

import json
import os
import traceback
from datetime import datetime, timedelta
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .classifier import classify
from .fallback import call_with_fallback
from .router import get_best_model, health_scores
from .telemetry import get_recent_requests, get_stats, log_request
from .toon_layer import count_tokens, to_toon

# Load API keys from environment
os.environ.setdefault("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
os.environ.setdefault("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
os.environ.setdefault("HF_TOKEN", os.environ.get("HF_TOKEN", ""))

app = FastAPI()

# Rate limiting: track requests per IP per day
RATE_LIMIT_PER_DAY = 20
rate_limit_store: Dict[str, Dict] = {}  # {ip: {"count": int, "reset_time": datetime}}


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, accounting for proxies"""
    if x_forwarded_for := request.headers.get("X-Forwarded-For"):
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_reset_time() -> datetime:
    """Get next midnight UTC"""
    now_utc = datetime.utcnow()
    next_midnight = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return next_midnight


def check_rate_limit(ip: str) -> tuple[bool, dict]:
    """
    Check if IP has exceeded rate limit for today.
    Returns (is_allowed, info_dict)
    """
    now_utc = datetime.utcnow()

    if ip not in rate_limit_store:
        rate_limit_store[ip] = {"count": 0, "reset_time": get_reset_time()}

    record = rate_limit_store[ip]

    # Reset if past the reset time
    if now_utc >= record["reset_time"]:
        record["count"] = 0
        record["reset_time"] = get_reset_time()

    if record["count"] >= RATE_LIMIT_PER_DAY:
        return False, {
            "error": "Daily limit reached. Come back tomorrow.",
            "limit": RATE_LIMIT_PER_DAY,
            "resets": "midnight UTC",
        }

    record["count"] += 1
    return True, {"count": record["count"], "limit": RATE_LIMIT_PER_DAY}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RouteRequest(BaseModel):
    prompt: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/limits")
def limits() -> dict:
    return {"requests_per_ip_per_day": RATE_LIMIT_PER_DAY, "resets": "midnight UTC"}


@app.get("/stats")
def stats() -> dict:
    return get_stats()


@app.get("/recent-requests")
def recent_requests() -> list[dict]:
    return get_recent_requests()


@app.get("/health-scores")
def health_scores_endpoint() -> dict:
    return health_scores


@app.post("/route")
def route_prompt(payload: RouteRequest, request: Request) -> dict:
    prompt = payload.prompt
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail={"error": "Prompt cannot be empty"})
    if len(prompt) > 5000:
        raise HTTPException(status_code=400, detail={"error": "Prompt too long"})

    # Check rate limit
    client_ip = get_client_ip(request)
    is_allowed, limit_info = check_rate_limit(client_ip)
    if not is_allowed:
        raise HTTPException(status_code=429, detail=limit_info)

    try:
        label, confidence = classify(prompt)
        model_label = label
        tier_blurred = False
        if label == "COMPLEX" and confidence < 0.75:
            model_label = "MODERATE"
            tier_blurred = True
            print("[router] Tier blurring: COMPLEX -> MODERATE")
        elif label == "MODERATE" and confidence < 0.65:
            model_label = "SIMPLE"
            tier_blurred = True
            print("[router] Tier blurring: MODERATE -> SIMPLE")

        model = get_best_model(model_label)

        toon_payload = to_toon({"prompt": prompt})
        toon_tokens = count_tokens(toon_payload)
        json_payload = json.dumps({"prompt": prompt})
        json_tokens = count_tokens(json_payload)

        result = call_with_fallback(prompt, model)

        try:
            log_request(
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
            # Telemetry failures must not break the API response in serverless environments
            print(f"Telemetry error (non-fatal): {e}")

        return {
            "response": result["response"],
            "model_used": result["model_used"],
            "label": label,
            "confidence": confidence,
            "latency_ms": result["latency_ms"],
            "toon_tokens": toon_tokens,
            "json_tokens": json_tokens,
            "tier_blurred": tier_blurred,
            "fallback_used": result.get("fallback_used", False),
        }
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"error": "Internal server error"})
