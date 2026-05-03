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
