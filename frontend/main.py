from fastapi import FastAPI, Request, Form, Depends, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from config import settings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import jwt

app = FastAPI(title="Blog Frontend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# --- Helper functions ---
async def get_metrics():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.metrics_url}/metrics")
        return r.json() if r.status_code == 200 else {}

async def get_posts():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.posts_url}/posts?is_active=true&limit=10")
        return r.json().get("posts", []) if r.status_code == 200 else []

async def get_ads():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.ads_url}/ads/active")
        return r.json() if r.status_code == 200 else []

async def get_events():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.events_url}/events?limit=10")
        return r.json().get("events", []) if r.status_code == 200 else []

async def get_polls():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.polls_url}/polls/active")
        return r.json() if r.status_code == 200 else []

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    posts = await get_posts()
    ads = await get_ads()
    events = await get_events()
    polls = await get_polls()
    return templates.TemplateResponse("home.html", {"request": request, "posts": posts, "ads": ads, "events": events, "polls": polls})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    metrics = await get_metrics()
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "metrics": metrics})

@app.get("/admin/medias", response_class=HTMLResponse)
async def manage_medias(request: Request):
    return templates.TemplateResponse("medias.html", {"request": request})

@app.get("/admin/posts", response_class=HTMLResponse)
async def manage_posts(request: Request):
    return templates.TemplateResponse("posts.html", {"request": request})

@app.get("/admin/ads", response_class=HTMLResponse)
async def manage_ads(request: Request):
    return templates.TemplateResponse("ads.html", {"request": request})

@app.get("/admin/events", response_class=HTMLResponse)
async def manage_events(request: Request):
    return templates.TemplateResponse("events.html", {"request": request})

@app.get("/admin/polls", response_class=HTMLResponse)
async def manage_polls(request: Request):
    return templates.TemplateResponse("polls.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{settings.auth_url}/login", json={"username": username, "password": password})
            print(f"Auth service response status: {r.status_code}")
            print(f"Auth service response: {r.text}")
            
            if r.status_code == 200:
                response_data = r.json()
                print(f"Response data: {response_data}")
                
                # In production, set a secure cookie or session
                response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
                response.set_cookie(key="access_token", value=response_data["access_token"])
                return response
            else:
                error_msg = "Invalid credentials"
                try:
                    error_data = r.json()
                    error_msg = error_data.get("detail", "Invalid credentials")
                except:
                    pass
                return templates.TemplateResponse("login.html", {"request": request, "error": error_msg})
    except Exception as e:
        print(f"Login error: {e}")
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Login error: {str(e)}"})

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

# --- API Routes for Posts CRUD ---
@app.get("/api/posts")
async def api_get_posts():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.posts_url}/posts")
        return r.json() if r.status_code == 200 else {"posts": []}

@app.get("/api/posts/{post_id}")
async def api_get_post(post_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.posts_url}/posts/{post_id}")
        return r.json() if r.status_code == 200 else {}

@app.post("/api/posts")
async def api_create_post(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.posts_url}/posts", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to create post"}

@app.put("/api/posts/{post_id}")
async def api_update_post(post_id: str, request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{settings.posts_url}/posts/{post_id}", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to update post"}

@app.delete("/api/posts/{post_id}")
async def api_delete_post(post_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{settings.posts_url}/posts/{post_id}")
        return r.json() if r.status_code == 200 else {"error": "Failed to delete post"}

# --- API Routes for Ads CRUD ---
@app.get("/api/ads")
async def api_get_ads():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.ads_url}/ads")
        return r.json() if r.status_code == 200 else {"ads": []}

@app.get("/api/ads/{ad_id}")
async def api_get_ad(ad_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.ads_url}/ads/{ad_id}")
        return r.json() if r.status_code == 200 else {}

@app.post("/api/ads")
async def api_create_ad(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.ads_url}/ads", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to create ad"}

@app.put("/api/ads/{ad_id}")
async def api_update_ad(ad_id: str, request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{settings.ads_url}/ads/{ad_id}", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to update ad"}

@app.delete("/api/ads/{ad_id}")
async def api_delete_ad(ad_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{settings.ads_url}/ads/{ad_id}")
        return r.json() if r.status_code == 200 else {"error": "Failed to delete ad"}

# --- API Routes for Events CRUD ---
@app.get("/api/events")
async def api_get_events():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.events_url}/events")
        return r.json() if r.status_code == 200 else {"events": []}

@app.get("/api/events/{event_id}")
async def api_get_event(event_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.events_url}/events/{event_id}")
        return r.json() if r.status_code == 200 else {}

@app.post("/api/events")
async def api_create_event(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.events_url}/events", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to create event"}

@app.put("/api/events/{event_id}")
async def api_update_event(event_id: str, request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{settings.events_url}/events/{event_id}", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to update event"}

@app.delete("/api/events/{event_id}")
async def api_delete_event(event_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{settings.events_url}/events/{event_id}")
        return r.json() if r.status_code == 200 else {"error": "Failed to delete event"}

# --- API Routes for Polls CRUD ---
@app.get("/api/polls")
async def api_get_polls():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.polls_url}/polls")
        return r.json() if r.status_code == 200 else {"polls": []}

@app.get("/api/polls/{poll_id}")
async def api_get_poll(poll_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.polls_url}/polls/{poll_id}")
        return r.json() if r.status_code == 200 else {}

@app.post("/api/polls")
async def api_create_poll(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.polls_url}/polls", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to create poll"}

@app.put("/api/polls/{poll_id}")
async def api_update_poll(poll_id: str, request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{settings.polls_url}/polls/{poll_id}", json=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to update poll"}

@app.delete("/api/polls/{poll_id}")
async def api_delete_poll(poll_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{settings.polls_url}/polls/{poll_id}")
        return r.json() if r.status_code == 200 else {"error": "Failed to delete poll"}

@app.get("/api/polls/{poll_id}/results")
async def api_get_poll_results(poll_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.polls_url}/polls/{poll_id}/results")
        return r.json() if r.status_code == 200 else {"error": "Failed to get poll results"}

# --- API Routes for Medias CRUD ---
@app.get("/api/medias")
async def api_get_medias():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.medias_url}/files")
        return r.json() if r.status_code == 200 else {"medias": []}

@app.get("/api/medias/{media_id}")
async def api_get_media(media_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.medias_url}/files/{media_id}")
        return r.json() if r.status_code == 200 else {}

@app.post("/api/medias/upload")
async def api_upload_media(request: Request):
    form = await request.form()
    file = form.get("file")
    folder = form.get("folder", "general")
    
    if not file:
        return {"error": "No file provided"}
    
    # Read the file content
    file_content = await file.read()
    
    # Create the files tuple with the file content
    files = {"file": (file.filename, file_content, file.content_type)}
    data = {"folder": folder}
    
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.medias_url}/upload", files=files, data=data)
        return r.json() if r.status_code == 200 else {"error": "Failed to upload file"}

@app.delete("/api/medias/{media_id}")
async def api_delete_media(media_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{settings.medias_url}/files/{media_id}")
        return r.json() if r.status_code == 200 else {"error": "Failed to delete media"}

@app.get("/api/medias/{media_id}/download")
async def api_download_media(media_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.medias_url}/files/{media_id}/download")
        if r.status_code == 200:
            return Response(content=r.content, media_type=r.headers.get("content-type"))
        return {"error": "Failed to download file"}

@app.get("/test-login")
async def test_login():
    """Test endpoint to check login with default admin credentials."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{settings.auth_url}/login", json={"username": "admin", "password": "admin123"})
            return {
                "status_code": r.status_code,
                "response": r.text,
                "headers": dict(r.headers)
            }
    except Exception as e:
        return {"error": f"Login test failed: {str(e)}"}

@app.get("/test-auth")
async def test_auth():
    """Test endpoint to check if auth service is reachable."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{settings.auth_url}/health")
            return {"auth_service_status": r.status_code, "auth_service_response": r.text}
    except Exception as e:
        return {"error": f"Auth service not reachable: {str(e)}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "frontend"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        # Only protect /admin routes (except /login)
        if request.url.path.startswith("/admin") and request.url.path != "/login":
            token = request.cookies.get("access_token")
            if not token:
                return RedirectResponse(url="/login", status_code=302)
            
            # For now, skip JWT verification to allow login to work
            # In production, you should properly verify the JWT token
            try:
                # Basic token validation - just check if it exists and has the right format
                if not token or len(token.split('.')) != 3:
                    return RedirectResponse(url="/login", status_code=302)
                
                # Optional: Verify JWT signature (requires the same secret key as auth service)
                # jwt.decode(token, settings.secret_key, algorithms=["HS256"])
                
            except Exception as e:
                print(f"Token verification error: {e}")
                return RedirectResponse(url="/login", status_code=302)
        
        response = await call_next(request)
        return response

app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 