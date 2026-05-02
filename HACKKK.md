# OmniRoute AI: Intelligent LLM Routing System
**Hackathon Execution Plan (24-Hour Sprint)**

## 1. The Core Objective
Build a high-performance middleware gateway that dynamically routes LLM requests to optimize for **Cost**, **Latency**, and **Quality** — using zero-cost local classification, real-time provider health scoring, TOON-formatted payloads, and a live savings counter dashboard.

---

## 2. Technical Architecture (The MVP)

### A. The Triage Layer — Zero-Cost Local Classification
- **Approach:** Replace the LLM-based classifier with a **local sentence-transformer model** (`all-MiniLM-L6-v2` via HuggingFace) that embeds and classifies prompts in **<5ms with zero API cost**.
- **Implementation:** Fine-tune or prompt-engineer the transformer to output exactly one of three labels: `SIMPLE`, `MODERATE`, or `COMPLEX`.
- **Fast-Path:** Local keyword-based cache for trivial prompts (e.g., "Hi", "Help") to bypass the classifier entirely.
- **Why this wins:** No extra LLM call, no added latency, no added cost. Judges see classification happening instantly on-device.

### B. TOON Payload Layer — Token Reduction at the Source
- **Approach:** All prompts and structured API payloads are serialized in **TOON (Token-Oriented Object Notation)** before being sent to any model.
- **What it does:** Eliminates redundant JSON syntax (braces, brackets, repeated keys) using indentation and tabular structures — reducing token usage by **30–60%** with lossless round-tripping to/from JSON.
- **Implementation:** Use the `@toon-format/toon` TypeScript library to convert incoming structured prompts to TOON before injection into the LLM call.
- **Why this wins:** OmniRoute optimizes tokens *before* routing even begins. No other team will have this. Pitch it as: *"TOON-encoded payloads cut token overhead by up to 60% at the input layer."*

### C. The Routing Matrix — Genuinely Dynamic Selection
Routing is determined by the classification label AND real-time provider health:

| Label | Target Model | Priority | Goal |
| :--- | :--- | :--- | :--- |
| **SIMPLE** | `Mistral-7B-Instruct-v0.3` | HuggingFace (Free) | Minimum cost, near-instant response. |
| **MODERATE** | `Mixtral-8x7B-Instruct` | Groq (Free) | High logic, reasonable speed. |
| **COMPLEX** | `Llama-3.1-70B-Instruct` | Groq / HuggingFace (Free) | Max reasoning, regardless of cost/speed. |
| **Fallback** | `gemini-1.5-flash` | Google AI Studio (Free) | Safety net if other providers are rate-limited. |

**Real-Time Provider Health Scoring:**
- Maintain a live score per provider based on **rolling average latency + error rate** from the last N requests.
- Route to the *currently fastest healthy provider* for that complexity tier — not a hardcoded one.
- If latency exceeds 2s threshold, mark endpoint as "Degraded" and route around it automatically.

**Confidence-Based Tier Blurring:**
- If classifier confidence is borderline (e.g., 60% MODERATE / 40% COMPLEX), route to MODERATE first.
- If response quality is low, auto-escalate to COMPLEX. Now routing is genuinely adaptive.

### D. Reliability & Performance Layer
- **Unified API:** Use **LiteLLM** as the core library — no separate wrappers for different providers.
- **Fallback Chain:** `Primary Model` → `Secondary Model` → `Tertiary Model` on 429 (Rate Limit) or 500 (Error).
- **Latency Tracking:** Track Time-to-First-Token (TTFT) per provider. Feed into health scoring above.

### E. The Adaptive Feedback Loop
- **Storage:** **SQLite** database logs: `Prompt` | `TOON Token Count` | `JSON Token Count` | `Classified Level` | `Model Used` | `Latency` | `Cost` | `User Feedback`.
- **Learning:** If a `SIMPLE` request is flagged "Bad", add that prompt pattern to a "Complexity Upgrade" list for future routing.

---

## 3. The Demo Moment — Live Savings Counter (Priority 2)

This is the feature judges remember. Build a live dashboard panel that shows:

- **Savings Meter:** Every time a SIMPLE query routes to `Mistral-7B` instead of `Llama-3.1-70B`, display the token count delta and compute-cost equivalent in real time (use public HuggingFace/Groq pricing as the baseline).
- **TOON vs JSON counter:** Side-by-side token count for each request showing how many tokens TOON saved vs raw JSON.
- **Side-by-side benchmark:** Same 20 test queries through OmniRoute vs "naive always-use-biggest-model" — display total tokens used, total latency, and quality score.
- **Projected scale:** At 1M requests/day → *"OmniRoute saves X million tokens/month vs. always routing to the largest model."* Give judges a headline number.

The pitch line: *"We saved 73% cost with <2% quality degradation."*

---

## 4. 24-Hour Implementation Roadmap

> **How we're working:** Vibe coding — move fast, ship working code, understand what you built before adding more.

### Phase 1 — Build & Test Core (Hours 0–12)
*Get everything working end-to-end before touching the UI or extra features. Nothing moves to Phase 2 unless Phase 1 is fully tested.*

| Window | Task | Deliverable |
| :--- | :--- | :--- |
| **Hours 0–3** | **Core Pipeline** | FastAPI server + LiteLLM + 3+ providers connected. Basic prompt → response working. |
| **Hours 3–6** | **TOON + Classifier** | TOON serialization integrated. `all-MiniLM-L6-v2` running locally, outputting SIMPLE / MODERATE / COMPLEX. |
| **Hours 6–9** | **Routing + Reliability** | Routing Matrix live. Fallback chains (429/500). Real-time provider health scoring active. |
| **Hours 9–12** | **Telemetry + Full Pipeline Test** | SQLite logging running. Full flow tested end-to-end: prompt → classify → TOON → route → fallback → log. All blockers fixed. |

### Phase 2 — Features & Changes (Hours 12–18)
*Only add what strengthens the demo. If something from Phase 1 needs fixing, fix it here first. Don't add new features on top of broken foundations.*

| Window | Task | Deliverable |
| :--- | :--- | :--- |
| **Hours 12–15** | **Dashboard** | React/Next.js UI showing routing decisions, model used, latency, cost per request. |
| **Hours 15–18** | **Live Savings Counter** *(Priority 2)* | Savings meter live. TOON vs JSON token counter. Benchmark view with projected scale numbers. |

### Phase 3 — Test, Understand & Demo Prep (Hours 18–24)
*No new features. This is your time to actually understand what you vibe-coded, rehearse the demo, and make sure nothing breaks under pressure.*

| Window | Task | Deliverable |
| :--- | :--- | :--- |
| **Hours 18–20** | **End-to-End Testing** | Run the full demo flow 3+ times. Break it intentionally. Fix what you find. |
| **Hours 20–22** | **Code Walkthrough** | Go through every module together — understand what each part does and why. You need to answer judge questions confidently. |
| **Hours 22–24** | **Demo Script + Final Polish** | Lock the demo script. Prepare the pitch line. Clean up the UI. |

---

## 5. Prerequisites — Before You Write a Single Line of Code

Everything in this list should be ready **before the hackathon clock starts.**

### API Keys & Accounts — 100% Free Stack
- [ ] **HuggingFace account** ✅ already have — generate an **Access Token** at `huggingface.co/settings/tokens`
  - Used for: `all-MiniLM-L6-v2` classifier + `Mistral-7B` + `Llama-3.1-70B` Inference API
- [ ] **Groq API key** — sign up free at `console.groq.com` (no credit card needed)
  - Used for: `Mixtral-8x7B` (MODERATE) and `Llama-3.1-70B` (COMPLEX) — Groq is faster than OpenAI for these models
- [ ] **Google AI Studio key** — free at `aistudio.google.com/app/apikey`
  - Used for: `gemini-1.5-flash` (SIMPLE tier backup) — very generous free quota
- [ ] **Vercel account** ✅ already have — ready for deployment
- [ ] Confirm all 3 keys work with a quick test call **before** the hackathon starts

### Free Routing Matrix
| Label | Model | Provider | Cost |
| :--- | :--- | :--- | :--- |
| **SIMPLE** | `mistralai/Mistral-7B-Instruct-v0.3` | HuggingFace Inference API | Free |
| **MODERATE** | `mixtral-8x7b-32768` | Groq | Free |
| **COMPLEX** | `llama-3.1-70b-versatile` | Groq | Free |
| **Fallback** | `gemini-1.5-flash` | Google AI Studio | Free |

### Local Environment
- [ ] **Python 3.10+** installed and working (`python --version`)
- [ ] **Node.js 18+** and `npm` installed (`node --version`)
- [ ] **Git** installed and a repo created
- [ ] Pre-install Python packages and confirm zero errors:
  ```
  pip install fastapi uvicorn litellm sentence-transformers
  ```
- [ ] Pre-install Node packages and confirm:
  ```
  npm install @toon-format/toon
  ```

### Project Structure — Create This Before Hour 0
```
omni-route/
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── classifier.py    # sentence-transformer logic
│   ├── router.py        # routing matrix + health scoring
│   ├── toon_layer.py    # TOON serialization
│   ├── telemetry.py     # SQLite logging
│   └── fallback.py      # fallback chain logic
├── frontend/
│   └── (Next.js app)
├── .env                 # all API keys go here, never hardcode
└── requirements.txt
```

### Knowledge — Skim These Before You Start
- [ ] **LiteLLM docs** — how to call multiple providers with one interface (`litellm.completion`)
- [ ] **sentence-transformers quickstart** — loading `all-MiniLM-L6-v2` and running inference
- [ ] **TOON spec** — `github.com/toon-format/spec` — understand the syntax so you can explain it to judges
- [ ] **FastAPI basics** — if anyone on the team hasn't used it, 20 minutes now saves 2 hours during the sprint

### Team Alignment
- [ ] Decide who owns Backend, Frontend, and Demo/Pitch — no overlaps
- [ ] **Rule:** Phase 1 is non-negotiable. No one touches the frontend until the backend pipeline is fully tested
- [ ] Share `.env` file securely — not over chat, use a password manager or encrypted note

---

## 6. Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python, FastAPI |
| **Local Classifier** | HuggingFace `all-MiniLM-L6-v2` (sentence-transformers) |
| **Payload Format** | TOON via `@toon-format/toon` (TypeScript) |
| **LLM Integration** | LiteLLM |
| **Database** | SQLite (telemetry + feedback) |
| **Frontend** | Next.js / Tailwind CSS |
| **Deployment** | Vercel / Railway |

---

## 7. The Pitch — What Makes OmniRoute Different

> *"Every other routing system adds an LLM call to decide which LLM to call. OmniRoute classifies in 5ms locally, compresses prompts 30–60% with TOON before sending, and routes to the healthiest provider in real time. The result: lower cost, lower latency, and a system that actually gets smarter over time."*

**Three defensible technical edges:**
1. Zero-cost local classification (no extra API call)
2. TOON payload compression (30–60% token reduction before routing)
3. Real-time provider health scoring (dynamic, not a lookup table)
