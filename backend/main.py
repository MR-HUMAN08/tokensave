from __future__ import annotations

import json
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .classifier import classify
from .fallback import call_with_fallback
from .router import get_best_model, health_scores
from .telemetry import get_recent_requests, get_stats, log_request
from .toon_layer import count_tokens, to_toon


load_dotenv()

app = FastAPI()

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
def route_prompt(payload: RouteRequest) -> dict:
    prompt = payload.prompt
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail={"error": "Prompt cannot be empty"})
    if len(prompt) > 5000:
        raise HTTPException(status_code=400, detail={"error": "Prompt too long"})

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
