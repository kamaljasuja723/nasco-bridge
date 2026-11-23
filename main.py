from fastapi import FastAPI, Request, HTTPException
import requests
import os

app = FastAPI()

# Render Environment Settings
NASCO_TOKEN_URL = os.getenv("NASCO_TOKEN_URL", "https://test.api.nasco.com/oauth2/tokens/v1")
NASCO_CLIENT_ID = os.getenv("NASCO_CLIENT_ID", "AaXprGstSrhY9qRObY9Le4HlwkqSYH96")
NASCO_CLIENT_SECRET = os.getenv("NASCO_CLIENT_SECRET", "whCMIvuUVpExjt5o")
NASCO_API_URL = os.getenv("NASCO_API_URL", "https://test.api.nasco.com")

DISCOURSE_URL = "https://discourse.group"
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY", "3b1385abfa6a408e31effca56abd40bf8af3319d96b416f281be115a5c08db32")
DISCOURSE_USERNAME = "system"

# 1: Client ID Secret Key Access Token
def get_nasco_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": NASCO_CLIENT_ID,
        "client_secret": NASCO_CLIENT_SECRET
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(NASCO_TOKEN_URL, data=payload, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail=f"Token Error: {response.text}")
        
    return response.json().get("access_token")

@app.get("/")
def home():
    return {"message": "NASCO OAuth Middleware is Running!"}

# 2: Discourse NASCO API (Token)
@app.post("/discourse-to-nasco")
async def receive_from_discourse(request: Request):
    data = await request.json()
    
    if "topic" in data:
        # NASCO
        token = get_nasco_token()
        
        topic_title = data["topic"].get("title")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"title": topic_title}
        
        response = requests.post(NASCO_API_URL, json=payload, headers=headers)
        return {"status": "sent_to_nasco", "nasco_response": response.status_code}
    
    return {"status": "ignored"}

# 3: NASCO API Discourse (Token)
@app.get("/nasco-to-discourse")
def sync_nasco_to_discourse():
    # NASCO
    token = get_nasco_token()
    
    nasco_headers = {"Authorization": f"Bearer {token}"}
    nasco_res = requests.get(NASCO_API_URL, headers=nasco_headers)
    
    if nasco_res.status_code != 200:
        raise HTTPException(status_code=400, detail="NASCO API Error")
        
    nasco_data = nasco_res.json()
    
    discourse_headers = {
        "Api-Key": DISCOURSE_API_KEY,
        "Api-Username": DISCOURSE_USERNAME,
        "Content-Type": "application/json"
    }
    post_payload = {
        "title": f"NASCO Update: {nasco_data.get('name', 'New Data')}",
        "raw": f"NASCO : {str(nasco_data)}",
        "category": 1
    }
    
    d_res = requests.post(f"{DISCOURSE_URL}/posts.json", json=post_payload, headers=discourse_headers)
    return {"status": "posted_to_discourse", "discourse_status": d_res.status_code}
