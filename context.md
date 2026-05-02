# Context Notes

- 2026-05-02: Initialized OmniRoute AI backend scaffold and docs in omni-route/.
- 2026-05-02: Created backend files (main.py, classifier.py, router.py, fallback.py, toon_layer.py, telemetry.py), plus .env, .gitignore, requirements.txt.
- 2026-05-02: Created explanation.md and this context.md in T-HUB root.
- 2026-05-02: Created .venv and installed requirements with ./.venv/bin/pip.
- 2026-05-02: Started uvicorn for verification; POST /route calls failed due to missing API keys (HuggingFace 401, Groq invalid key). GET /stats and GET /health succeeded.
- 2026-05-02: Moved backend/, frontend/, .env, .gitignore, and requirements.txt from omni-route/ to the T-HUB root.
- 2026-05-02: Updated routing models to Groq (mistral-saba-24b, llama-3.3-70b-versatile) and compacted TOON formatting to avoid negative token savings.
- 2026-05-02: Updated SIMPLE routing model to groq/llama-3.1-8b-instant.
- 2026-05-02: Updated TOON formatting and JSON token counting to ensure positive token savings.
- 2026-05-02: Updated classifier heuristic to use keyword-based complexity tiers and length thresholds.
- 2026-05-02: Deleted backend/omni_route.db to reset telemetry; reran POST /route and GET /stats after reset.
- 2026-05-02: Added short-math exception and refined MODERATE keyword phrases in classifier.
- 2026-05-02: Updated MODERATE/COMPLEX routing to llama-3.3-70b-versatile and adjusted TOON encoding to reduce token counts.
