import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
 
# ADK imports — Runner executes the agent, InMemorySessionService manages sessions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
 
# Import our ADK agent defined in weather_agent/agent.py
from weather_agent.agent import root_agent
 
# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()
import os
print("GEMINI:", os.environ.get("GEMINI_API_KEY"))
print("WEATHER:", os.environ.get("API_KEY"))
# =============================================================================
# APP SETUP
# =============================================================================
 
app = FastAPI(
    title="Weather AI Agent",
    description="ADK + Gemini powered weather agent — Gen AI Academy APAC Track 1",
    version="1.0.0",
)
 
# Allow requests from any origin (needed for browser-based frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# =============================================================================
# ADK RUNNER SETUP
# =============================================================================
# InMemorySessionService stores conversation sessions in memory
# (each request gets its own session so they don't interfere)
session_service = InMemorySessionService()
 
# Runner is the ADK component that executes the agent
# It connects the agent, the session service, and the Gemini model together
runner = Runner(
    agent=root_agent,
    app_name="weather_agent",
    session_service=session_service,
)
 
# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================
 
class WeatherRequest(BaseModel):
    """Request body for POST /weather"""
    query: str  # Natural language weather question e.g. "What's the weather in Mumbai?"
 
class WeatherResponse(BaseModel):
    """Response body for POST /weather"""
    answer: str  # AI-generated weather response in plain text
 
# =============================================================================
# ROUTES
# =============================================================================
 
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serves the frontend UI.
    Reads index.html from the same directory and returns it as HTML.
    """
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback if index.html is missing
        return HTMLResponse(content="<h2>✅ Weather AI Agent is running!</h2>")
 
 
@app.get("/health")
async def health():
    """
    Health check endpoint.
    Cloud Run and Railway use this to verify the container is running.
    """
    return {"status": "ok", "agent": root_agent.name}
 
 
@app.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """
    Main agent endpoint.
    Accepts a natural language weather query and returns an AI-generated response.
 
    Example request:
        POST /weather
        { "query": "Should I carry an umbrella in Delhi today?" }
 
    Example response:
        { "answer": "In Delhi, it is currently 28°C with light rain..." }
    """
    # Validate the query is not empty
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
 
    # Create a unique session for each request
    # This ensures conversations don't mix between different users
    session_id = f"session_{abs(hash(request.query))}"
    user_id = "api_user"
 
    # Create a new ADK session for this request
    await session_service.create_session(
        app_name="weather_agent",
        user_id=user_id,
        session_id=session_id,
    )
 
    # Wrap the user query in ADK's Content format
    message = types.Content(
        role="user",
        parts=[types.Part(text=request.query)],
    )
 
    # Run the agent and collect the final response
    final_answer = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        # Wait for the final response event (after tool calls are done)
        if event.is_final_response():
            if event.content and event.content.parts:
                final_answer = event.content.parts[0].text
            break
 
    # Return error if agent didn't respond
    if not final_answer:
        raise HTTPException(status_code=500, detail="Agent did not return a response.")
 
    return WeatherResponse(answer=final_answer)
 
 
# =============================================================================
# ENTRY POINT
# =============================================================================
 
if __name__ == "__main__":
    # Read PORT from environment (Railway/Cloud Run set this automatically)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
 