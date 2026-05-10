# Paisa
Smart LLM Routing That Saves You Money

## Stack
- Backend: FastAPI + LiteLLM + sentence-transformers
- Frontend: Next.js + Tailwind CSS
- Models: Groq (Llama 3.1 8B, Llama 3.3 70B) + Google Gemini Flash
- DB: SQLite

## How to run

### Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload

### Frontend
cd frontend
npm install
npm run dev

## API Endpoints
- POST /route — classify and route a prompt
- GET /stats — aggregated telemetry
- GET /recent-requests — last 10 requests
- GET /health — health check
- GET /health-scores — live provider health scores

## How to Trigger a Release

To create a new release:
	git tag v0.1.7
	git push origin v0.1.7

This automatically:
1. Builds Windows .exe, Mac binary, Linux binary
2. Creates a GitHub Release with all 3 binaries attached
3. Publishes to PyPI

