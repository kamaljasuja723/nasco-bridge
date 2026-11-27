from fastapi import FastAPI, Request
import urllib.request
import json
import ssl
import os

app = FastAPI()

DISCOURSE_URL = "https://discourse.group"
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY", "3b1385abfa6a408e31effca56abd40bf8af3319d96b416f281be115a5c08db32")
DISCOURSE_USERNAME = "system"

# Create unverified SSL context to prevent certificate errors on cloud servers
ssl_context = ssl._create_unverified_context()

@app.get("/")
def home():
    return {"status": "online", "version": "v3-safe", "message": "Middleware is active!"}

# 1. Receive webhook data from Discourse and fetch live weather
@app.post("/discourse-to-nasco")
async def receive_from_discourse(request: Request):
    try:
        raw_body = await request.body()
        if not raw_body:
            return {"status": "success", "message": "Ping received successfully"}

        data = json.loads(raw_body.decode("utf-8"))

        # Fetch live weather for Jaipur using built-in urllib
        weather_url = "https://open-meteo.com"
        req = urllib.request.urlopen(weather_url, context=ssl_context, timeout=10)
        w_res = json.loads(req.read().decode("utf-8"))
        current_temp = w_res.get("current_weather", {}).get("temperature", "N/A")

        post_text = "No text found"
        if isinstance(data, dict):
            if "post" in data and isinstance(data["post"], dict):
                post_text = data["post"].get("cooked", "No text")
            elif "topic" in data and isinstance(data["topic"], dict):
                post_text = data["topic"].get("title", "No title")

        return {
            "status": "success",
            "received_from_discourse": post_text,
            "jaipur_live_temp_celsius": current_temp
        }
    except Exception as e:
        return {"status": "caught_error", "error_message": str(e)}

# 2. Fetch live weather data and post to Discourse
@app.get("/nasco-to-discourse")
def sync_weather_to_discourse():
    try:
        weather_url = "https://open-meteo.com"
        req = urllib.request.urlopen(weather_url, context=ssl_context, timeout=10)
        w_res = json.loads(req.read().decode("utf-8"))
        weather = w_res.get("current_weather", {})

        post_payload = json.dumps({
            "title": f"Jaipur Live Weather Update: {weather.get('temperature', 'N/A')}°C",
            "raw": f"Live weather data fetched from Open-Meteo API:\n- **Temperature:** {weather.get('temperature', 'N/A')}°C\n- **Wind Speed:** {weather.get('windspeed', 'N/A')} km/h",
            "category": 1
        }).encode("utf-8")

        d_req = urllib.request.Request(
            f"{DISCOURSE_URL}/posts.json",
            data=post_payload,
            headers={
                "Api-Key": DISCOURSE_API_KEY,
                "Api-Username": DISCOURSE_USERNAME,
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(d_req, context=ssl_context, timeout=10) as d_res:
            return {
                "status": "posted_to_discourse",
                "discourse_status": d_res.status,
                "response": json.loads(d_res.read().decode("utf-8"))
            }
    except Exception as e:
        return {"status": "caught_error", "error_message": str(e)}
