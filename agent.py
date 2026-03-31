"""
Weather Agent - Built with Google ADK for Gen AI Academy APAC Track 1
Performs real-time weather lookups using OpenWeather API + Gemini tool-calling.
"""

import os
import requests
from google.adk.agents import Agent


def get_current_weather(city: str) -> dict:
    """
    Fetches real-time weather data for a given city using the OpenWeather API.

    Args:
        city: The name of the city to get weather for (e.g. "Chennai", "London").

    Returns:
        A dictionary containing temperature, condition, humidity, and wind speed,
        or an error message if the city is not found.
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "OpenWeather API key not configured."}

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={api_key}&units=metric"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature_celsius": data["main"]["temp"],
            "feels_like_celsius": data["main"]["feels_like"],
            "condition": data["weather"][0]["description"],
            "humidity_percent": data["main"]["humidity"],
            "wind_speed_mps": data["wind"]["speed"],
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"City '{city}' not found. Please check the spelling."}
        return {"error": f"Weather service returned an error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Could not reach the weather service: {str(e)}"}


# ── ADK Root Agent ────────────────────────────────────────────────────────────

root_agent = Agent(
    name="weather_agent",
    model="gemini-2.0-flash",
    description=(
        "An AI weather assistant that fetches real-time weather data "
        "and answers questions in a friendly, conversational way."
    ),
    instruction=(
        "You are a helpful weather assistant. "
        "When a user asks about weather for any location, use the "
        "get_current_weather tool to fetch live data. "
        "Then give a friendly, plain-text response that includes: "
        "the temperature, weather condition, humidity, wind speed, "
        "and any helpful advice (e.g. carry an umbrella, stay hydrated). "
        "Do not use markdown formatting — respond in plain text only."
    ),
    tools=[get_current_weather],
)
