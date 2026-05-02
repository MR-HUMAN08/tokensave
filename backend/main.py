from __future__ import annotations

import json

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .classifier import classify
from .fallback import call_with_fallback
from .router import get_model, update_health
from .telemetry import get_stats, log_request
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


@app.post("/route")
def route_prompt(payload: RouteRequest) -> dict:
    prompt = payload.prompt
    label = classify(prompt)
    model = get_model(label)

    toon_payload = to_toon({"prompt": prompt})
    toon_tokens = count_tokens(toon_payload)
    json_payload = json.dumps({"prompt": prompt})
    json_tokens = count_tokens(json_payload)

    result = call_with_fallback(prompt, model)
    update_health(result["model_used"], result["latency_ms"], not result["success"])

    log_request(
        prompt=prompt,
        label=label,
        model_used=result["model_used"],
        latency_ms=result["latency_ms"],
        toon_tokens=toon_tokens,
        json_tokens=json_tokens,
    )

    return {
        "response": result["response"],
        "model_used": result["model_used"],
        "label": label,
        "latency_ms": result["latency_ms"],
        "toon_tokens": toon_tokens,
        "json_tokens": json_tokens,
    }
