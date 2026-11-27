from fastapi import FastAPI, Request
import httpx
import json
import os

app = FastAPI()

# Discourse credentials (set DISCOURSE_API_KEY in Render Environment Variables)
DISCOURSE_URL = "https://discourse.group"
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY", "3b1385abfa6a408e31effca56abd40bf8af3319d96b416f281be115a5c08db32")
DISCOURSE_USERNAME = "system"

@app.get("/")
def home():
    return {
        "status": "online",
        "version": "v8-full-weather-discourse",
        "discourse_key_configured": DISCOURSE_API_KEY != "YOUR_DISCOURSE_API_KEY"
    }

# 1. Discourse -> Middleware -> Weather API (No Discourse token needed for receiving webhooks)
@app.post("/discourse-to-nasco")
async def receive_from_discourse(request: Request):
    try:
        raw_body = await request.body()
        if not raw_body:
            return {"status": "success", "message": "Ping verified successfully"}

        data = json.loads(raw_body.decode("utf-8"))
        post_info = data.get("post", {})

        # Fetch live weather for Jaipur
        weather_url = "https://open-meteo.com"
        async with httpx.AsyncClient(timeout=10.0) as client:
            w_res = await client.get(weather_url)
            weather_data = w_res.json().get("current_weather", {})

        return {
            "status": "success",
            "discourse_post_received": post_info.get("raw", "N/A"),
            "jaipur_live_weather": {
                "temperature_celsius": weather_data.get("temperature"),
                "windspeed_kmh": weather_data.get("windspeed"),
                "time": weather_data.get("time")
            }
        }
    except Exception as e:
        return {"status": "caught_error", "error_message": str(e)}

# 2. Weather API -> Middleware -> Discourse Post (Uses DISCOURSE_API_KEY)
@app.get("/nasco-to-discourse")
async def sync_weather_to_discourse():
    try:
        weather_url = "https://open-meteo.com"
        async with httpx.AsyncClient(timeout=10.0) as client:
            w_res = await client.get(weather_url)
            weather = w_res.json().get("current_weather", {})

            post_payload = {
                "title": f"Jaipur Live Weather Report: {weather.get('temperature', 'N/A')}°C",
                "raw": f"Automated weather update fetched via Python Middleware:\n- **Temperature:** {weather.get('temperature', 'N/A')}°C\n- **Wind Speed:** {weather.get('windspeed', 'N/A')} km/h",
                "category": 4  # General category ID
            }

            discourse_headers = {
                "Api-Key": DISCOURSE_API_KEY,
                "Api-Username": DISCOURSE_USERNAME,
                "Content-Type": "application/json"
            }

            d_res = await client.post(
                f"{DISCOURSE_URL}/posts.json",
                json=post_payload,
                headers=discourse_headers
            )

            return {
                "status": "completed",
                "discourse_http_status": d_res.status_code,
                "discourse_response": d_res.json()
            }
    except Exception as e:
        return {"status": "caught_error", "error_message": str(e)}
