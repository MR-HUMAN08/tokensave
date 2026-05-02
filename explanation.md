# OmniRoute AI - Hackathon Judge Brief

OmniRoute AI is a FastAPI middleware that routes each LLM request to the most suitable free model, balancing cost, latency, and output quality in real time. Instead of making a second LLM call to decide routing, it classifies prompts locally using a small sentence-transformer model. This keeps classification fast, cheap, and consistent.

## What happens on each request
1. The prompt is classified as SIMPLE, MODERATE, or COMPLEX.
2. The router maps that label to a provider and model.
3. The request is sent using LiteLLM, with automatic fallback if the primary model is rate-limited or errors.
4. Telemetry is recorded in SQLite, including latency and token savings.

## Why it is different
- Zero-cost, local classification instead of paid model selection.
- Automatic routing to free models based on complexity tiers.
- Fallback handling and telemetry for reliability and demo insight.

## Demo highlights you can expect
- A health endpoint to verify the service is running.
- A routing endpoint that shows the selected model and latency.
- Stats that show request counts and token savings over time.
