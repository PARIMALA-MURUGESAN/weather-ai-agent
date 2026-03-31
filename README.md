# 🌤️ AI Weather Agent — ADK + Gemini + Cloud Run

> **Gen AI Academy APAC Edition — Track 1 Submission**
> Built with Google ADK, Gemini 2.0 Flash, and deployed on Cloud Run.

## What It Does
Answers natural language weather questions (e.g. *"Should I carry an umbrella in Mumbai?"*) using:
- **Google ADK** — agent framework with tool-calling
- **Gemini 2.0 Flash** — language model for reasoning
- **OpenWeather API** — real-time meteorological data
- **FastAPI** — HTTP server for the Cloud Run endpoint
- **Text-to-Speech** — browser-side voice output

---

## Project Structure
```
weather_adk_agent/
├── weather_agent/
│   ├── __init__.py       # Exposes root_agent
│   └── agent.py          # ADK Agent + weather tool definition
├── main.py               # FastAPI HTTP server (Cloud Run entry point)
├── index.html            # Frontend UI
├── requirements.txt
├── Dockerfile
├── .env.example
└── .gitignore
```

---

## Local Setup

### 1. Clone and install
```bash
git clone <your-repo-url>
cd weather_adk_agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set environment variables
```bash
cp .env.example .env
# Edit .env and add your real keys
```

### 3. Run locally
```bash
python main.py
# Visit http://localhost:8080
```

### 4. Test the API
```bash
curl -X POST http://localhost:8080/weather \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Chennai?"}'
```

---

## Deploy to Cloud Run

### Option A — gcloud CLI (Recommended)

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy directly from source (no Docker needed locally)
gcloud run deploy weather-agent \
  --source . \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key,OPENWEATHER_API_KEY=your_key
```

### Option B — Docker + Container Registry

```bash
# Build and push
docker build -t gcr.io/YOUR_PROJECT_ID/weather-agent .
docker push gcr.io/YOUR_PROJECT_ID/weather-agent

# Deploy
gcloud run deploy weather-agent \
  --image gcr.io/YOUR_PROJECT_ID/weather-agent \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key,OPENWEATHER_API_KEY=your_key
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Frontend UI |
| GET | `/health` | Health check |
| POST | `/weather` | Weather agent query |

### POST `/weather` — Request
```json
{ "query": "Is it going to rain in Delhi today?" }
```

### POST `/weather` — Response
```json
{ "answer": "In Delhi right now, it is 34°C with partly cloudy skies..." }
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | From [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `OPENWEATHER_API_KEY` | From [OpenWeatherMap](https://openweathermap.org/api) |
| `PORT` | Server port (default: 8080, set automatically by Cloud Run) |

---

## ⚠️ Security Notes
- **Never commit `.env` to Git** — it's in `.gitignore`
- Set secrets via `--set-env-vars` in gcloud or use **Google Secret Manager**
- Rotate any keys that were accidentally exposed
