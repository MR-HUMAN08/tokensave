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

## Release & CI

To create a new release and trigger CI builds:

	git tag v0.1.7
	git push origin v0.1.7

This will automatically:
1. Build Windows .exe, Mac binary, Linux binary
2. Create a GitHub Release with all 3 binaries attached
3. Publish the package to PyPI (requires `PYPI_TOKEN` secret)

Setup steps:
1. Add workflows in `.github/workflows/` (already included)
2. Add `PYPI_TOKEN` to repository secrets: `Settings` → `Secrets` → `Actions` → `New repository secret`
	 - Name: `PYPI_TOKEN`
	 - Value: your PyPI token (recommended: API token)

