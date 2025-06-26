from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import connect_to_mongo, close_mongo_connection, get_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog Metrics Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/metrics")
async def get_metrics():
    """Return counts for users, posts, ads, events, and polls."""
    try:
        # Users by status
        users_col = get_collection('users')
        user_statuses = ["active", "inactive", "pending"]
        user_counts = {}
        for status in user_statuses:
            user_counts[status] = await users_col.count_documents({"status": status})
        total_users = await users_col.count_documents({})
        user_counts["total"] = total_users

        # Posts
        posts_col = get_collection('posts')
        total_posts = await posts_col.count_documents({})

        # Ads by status
        ads_col = get_collection('ads')
        ad_statuses = [True, False]
        ad_counts = {"active": 0, "inactive": 0}
        ad_counts["active"] = await ads_col.count_documents({"is_active": True})
        ad_counts["inactive"] = await ads_col.count_documents({"is_active": False})
        ad_counts["total"] = await ads_col.count_documents({})

        # Events
        events_col = get_collection('events')
        total_events = await events_col.count_documents({})

        # Polls
        polls_col = get_collection('polls')
        total_polls = await polls_col.count_documents({})

        return {
            "users": user_counts,
            "posts": {"total": total_posts},
            "ads": ad_counts,
            "events": {"total": total_events},
            "polls": {"total": total_polls}
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "metrics"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 