from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

DISCOURSE_URL = "https://discourse.group"
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY", "YOUR_DISCOURSE_API_KEY")
DISCOURSE_USERNAME = "system"

@app.get("/")
def home():
    return {"message": "Weather Test Middleware is Running!"}

# 1. Receive webhook data from Discourse and fetch live weather from Open-Meteo API
@app.post("/discourse-to-nasco")
async def receive_from_discourse(request: Request):
    data = await request.json()
    
    # Open-Meteo Free Weather API (Live weather for Jaipur)
    weather_url = "https://open-meteo.com"
    w_res = requests.get(weather_url).json()
    current_temp = w_res.get("current_weather", {}).get("temperature")
    
    post_text = "Unknown"
    if "post" in data:
        post_text = data["post"].get("cooked", "")
    elif "topic" in data:
        post_text = data["topic"].get("title", "")

    return {
        "status": "success",
        "received_from_discourse": post_text,
        "jaipur_live_temp_celsius": current_temp
    }

# 2. Fetch live weather data from API and automatically create a new post in Discourse
@app.get("/nasco-to-discourse")
def sync_weather_to_discourse():
    weather_url = "https://open-meteo.com"
    w_res = requests.get(weather_url).json()
    weather = w_res.get("current_weather", {})
    
    discourse_headers = {
        "Api-Key": DISCOURSE_API_KEY,
        "Api-Username": DISCOURSE_USERNAME,
        "Content-Type": "application/json"
    }
    post_payload = {
        "title": f"Jaipur Live Weather Update: {weather.get('temperature')}°C",
        "raw": f"Live weather data fetched from Open-Meteo API:\n- **Temperature:** {weather.get('temperature')}°C\n- **Wind Speed:** {weather.get('windspeed')} km/h",
        "category": 1
    }
    
    d_res = requests.post(f"{DISCOURSE_URL}/posts.json", json=post_payload, headers=discourse_headers)
    return {
        "status": "posted_to_discourse",
        "discourse_status": d_res.status_code,
        "response": d_res.json()
    }
