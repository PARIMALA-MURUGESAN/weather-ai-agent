"""
main.py — HTTP entry point for the Weather ADK Agent on Cloud Run.

Exposes:
  GET  /         → health check
  POST /weather  → run the weather agent with a user query
"""

import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from weather_agent.agent import root_agent

# ── App & ADK setup ───────────────────────────────────────────────────────────

app = FastAPI(
    title="Weather AI Agent",
    description="ADK + Gemini powered weather agent deployed on Cloud Run",
    version="1.0.0",
)

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="weather_agent",
    session_service=session_service,
)


# ── Request / Response models ─────────────────────────────────────────────────

class WeatherRequest(BaseModel):
    query: str  # e.g. "What's the weather like in Chennai today?"


class WeatherResponse(BaseModel):
    answer: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serves the frontend UI."""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h2>Weather AI Agent is running ✅</h2>")


@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "ok", "agent": root_agent.name}


@app.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """
    Main agent endpoint. Accepts a natural language weather query
    and returns a friendly AI-generated response.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Each request gets its own session so conversations are independent
    session_id = f"session_{hash(request.query)}"
    user_id = "cloud_run_user"

    await session_service.create_session(
        app_name="weather_agent",
        user_id=user_id,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=request.query)],
    )

    final_answer = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_answer = event.content.parts[0].text
            break

    if not final_answer:
        raise HTTPException(status_code=500, detail="Agent did not return a response.")

    return WeatherResponse(answer=final_answer)


# ── CORS support (for browser-based front-end) ────────────────────────────────

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
