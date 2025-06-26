from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from bson import ObjectId
import logging
from typing import List, Optional

from config import settings
from database import connect_to_mongo, close_mongo_connection, get_collection
from models import Ad, AdCreate, AdUpdate, AdList

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog Ads Microservice", version="1.0.0")

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

@app.post("/ads", response_model=Ad)
async def create_ad(ad_data: AdCreate):
    """Create a new advertisement."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        ad_dict = ad_data.dict()
        ad_dict["created_at"] = datetime.utcnow()
        ad_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(ad_dict)
        ad_dict["id"] = str(result.inserted_id)
        
        return Ad(**ad_dict)
        
    except Exception as e:
        logger.error(f"Error creating ad: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating ad: {str(e)}")

@app.get("/ads", response_model=AdList)
async def list_ads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None)
):
    """List advertisements with optional filtering."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Build filter
        filter_query = {}
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        # Get total count
        total = await collection.count_documents(filter_query)
        
        # Get ads with pagination
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        ads = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for ad in ads:
            ad["id"] = str(ad["_id"])
        
        return AdList(
            ads=[Ad(**ad) for ad in ads],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing ads: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing ads: {str(e)}")

@app.get("/ads/active", response_model=List[Ad])
async def get_active_ads():
    """Get all active advertisements."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        cursor = collection.find({"is_active": True}).sort("created_at", -1)
        ads = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for ad in ads:
            ad["id"] = str(ad["_id"])
        
        return [Ad(**ad) for ad in ads]
        
    except Exception as e:
        logger.error(f"Error getting active ads: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting active ads: {str(e)}")

@app.get("/ads/{ad_id}", response_model=Ad)
async def get_ad(ad_id: str):
    """Get a specific advertisement by ID."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        ad = await collection.find_one({"_id": ObjectId(ad_id)})
        if not ad:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        ad["id"] = str(ad["_id"])
        return Ad(**ad)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ad: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting ad: {str(e)}")

@app.put("/ads/{ad_id}", response_model=Ad)
async def update_ad(ad_id: str, ad_update: AdUpdate):
    """Update an advertisement."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Get existing ad
        existing_ad = await collection.find_one({"_id": ObjectId(ad_id)})
        if not existing_ad:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        # Prepare update data
        update_data = ad_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the ad
        result = await collection.update_one(
            {"_id": ObjectId(ad_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        # Get updated ad
        updated_ad = await collection.find_one({"_id": ObjectId(ad_id)})
        updated_ad["id"] = str(updated_ad["_id"])
        
        return Ad(**updated_ad)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ad: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating ad: {str(e)}")

@app.delete("/ads/{ad_id}")
async def delete_ad(ad_id: str):
    """Delete an advertisement."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        result = await collection.delete_one({"_id": ObjectId(ad_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        return {"message": "Ad deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ad: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting ad: {str(e)}")

@app.post("/ads/{ad_id}/click")
async def record_ad_click(ad_id: str):
    """Record a click on an advertisement."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Check if ad exists
        ad = await collection.find_one({"_id": ObjectId(ad_id)})
        if not ad:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        # Increment click count (you might want to add a clicks field to your model)
        await collection.update_one(
            {"_id": ObjectId(ad_id)},
            {"$inc": {"clicks": 1}}
        )
        
        return {"message": "Click recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording ad click: {e}")
        raise HTTPException(status_code=500, detail=f"Error recording ad click: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ads"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 