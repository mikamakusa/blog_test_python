from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from bson import ObjectId
import logging
from typing import List, Optional

from config import settings
from database import connect_to_mongo, close_mongo_connection, get_collection
from models import Post, PostCreate, PostUpdate, PostList
from utils import markdown_to_html

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog Posts Microservice", version="1.0.0")

# CORS middleware
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

@app.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate):
    """Create a new blog post."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        post_dict = post_data.dict()
        post_dict["created_at"] = datetime.utcnow()
        post_dict["updated_at"] = datetime.utcnow()
        post_dict["html_content"] = markdown_to_html(post_data.content)
        
        result = await collection.insert_one(post_dict)
        post_dict["id"] = str(result.inserted_id)
        
        return Post(**post_dict)
        
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")

@app.get("/posts", response_model=PostList)
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    author: Optional[str] = Query(None)
):
    """List blog posts with optional filtering."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Build filter
        filter_query = {}
        if is_active is not None:
            filter_query["is_active"] = is_active
        if author:
            filter_query["author"] = {"$regex": author, "$options": "i"}
        
        # Get total count
        total = await collection.count_documents(filter_query)
        
        # Get posts with pagination
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        posts = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for post in posts:
            post["id"] = str(post["_id"])
        
        return PostList(
            posts=[Post(**post) for post in posts],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing posts: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing posts: {str(e)}")

@app.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: str):
    """Get a specific blog post by ID."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        post = await collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post["id"] = str(post["_id"])
        return Post(**post)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting post: {str(e)}")

@app.put("/posts/{post_id}", response_model=Post)
async def update_post(post_id: str, post_update: PostUpdate):
    """Update a blog post."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Get existing post
        existing_post = await collection.find_one({"_id": ObjectId(post_id)})
        if not existing_post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Prepare update data
        update_data = post_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update HTML content if content is being updated
        if "content" in update_data:
            update_data["html_content"] = markdown_to_html(update_data["content"])
        
        # Update the post
        result = await collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Get updated post
        updated_post = await collection.find_one({"_id": ObjectId(post_id)})
        updated_post["id"] = str(updated_post["_id"])
        
        return Post(**updated_post)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating post: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    """Delete a blog post."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        result = await collection.delete_one({"_id": ObjectId(post_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return {"message": "Post deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting post: {str(e)}")

@app.get("/posts/{post_id}/html")
async def get_post_html(post_id: str):
    """Get the HTML content of a blog post."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        post = await collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return {"html_content": post.get("html_content", "")}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post HTML: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting post HTML: {str(e)}")

@app.get("/posts/search/{query}")
async def search_posts(query: str, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    """Search posts by title, description, or content."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Create search filter
        search_filter = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Get total count
        total = await collection.count_documents(search_filter)
        
        # Get posts with pagination
        cursor = collection.find(search_filter).skip(skip).limit(limit).sort("created_at", -1)
        posts = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for post in posts:
            post["id"] = str(post["_id"])
        
        return PostList(
            posts=[Post(**post) for post in posts],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error searching posts: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching posts: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "posts"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 