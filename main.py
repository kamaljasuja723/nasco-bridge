from fastapi import FastAPI, Request
import urllib.request
import json
import ssl
import os

app = FastAPI()

DISCOURSE_URL = "https://discourse.group"
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY", "3b1385abfa6a408e31effca56abd40bf8af3319d96b416f281be115a5c08db32")
DISCOURSE_USERNAME = "system"

ssl_context = ssl._create_unverified_context()

def call_external_api(url, payload=None):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data_bytes = json.dumps(payload).encode("utf-8") if payload else None
    method = "POST" if payload else "GET"
    
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    with urllib.request.urlopen(req, context=ssl_context, timeout=10) as res:
        raw_text = res.read().decode("utf-8")
        return json.loads(raw_text) if raw_text else {"status": "empty_response"}

@app.get("/")
def home():
    return {"status": "online", "version": "v5-demo-ready", "message": "Middleware is active!"}

# 1. Receive post from Discourse and forward it to External Test API
@app.post("/discourse-to-nasco")
async def receive_from_discourse(request: Request):
    try:
        raw_body = await request.body()
        if not raw_body:
            return {"status": "success", "message": "Ping received successfully"}

        data = json.loads(raw_body.decode("utf-8"))
        
        # Extract post details from Discourse payload
        post_info = data.get("post", {})
        title = post_info.get("topic_title", "New Discourse Post")
        content = post_info.get("raw", "No content")
        author = post_info.get("username", "unknown")

        # Send this data to External Test API (Simulating NASCO API)
        test_api_url = "https://typicode.com"
        api_response = call_external_api(test_api_url, {
            "title": title,
            "body": content,
            "user": author
        })

        return {
            "status": "success",
            "message": "Data successfully synced from Discourse to External API",
            "discourse_post_received": {
                "title": title,
                "content": content,
                "author": author
            },
            "external_api_response": api_response
        }
    except Exception as e:
        return {"status": "caught_error", "error_message": str(e)}

# 2. Fetch data from External API and create a new post in Discourse
@app.get("/nasco-to-discourse")
def sync_external_to_discourse():
    try:
        # Fetch sample data from External Test API
        ext_data = call_external_api("https://typicode.com/1")

        post_payload = {
            "title": f"API Sync Test: {ext_data.get('title', 'Sample Title')[:40]}",
            "raw": f"Automated post created via Python Middleware:\n\n> {ext_data.get('body', '')}",
            "category": 4  # General category ID from your Discourse payload
        }

        d_res = call_external_api(f"{DISCOURSE_URL}/posts.json", post_payload)
        return {
            "status": "posted_to_discourse",
            "discourse_post_id": d_res.get("id"),
            "topic_url": f"{DISCOURSE_URL}/t/{d_res.get('topic_slug')}/{d_res.get('topic_id')}"
        }
    except Exception as e:
        return {"status": "caught_error", "error_message": str(e)}
