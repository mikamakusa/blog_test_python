from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from bson import ObjectId
import logging
from typing import List, Optional

from config import settings
from database import connect_to_mongo, close_mongo_connection, get_collection
from models import Event, EventCreate, EventUpdate, EventList

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog Events Microservice", version="1.0.0")

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

@app.post("/events", response_model=Event)
async def create_event(event_data: EventCreate):
    """Create a new event."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        event_dict = event_data.dict()
        event_dict["created_at"] = datetime.utcnow()
        event_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(event_dict)
        event_dict["id"] = str(result.inserted_id)
        
        return Event(**event_dict)
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@app.get("/events", response_model=EventList)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    upcoming: Optional[bool] = Query(None),
    past: Optional[bool] = Query(None)
):
    """List events with optional filtering."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Build filter
        filter_query = {}
        now = datetime.utcnow()
        
        if upcoming is not None:
            if upcoming:
                filter_query["date_start"] = {"$gte": now}
            else:
                filter_query["date_start"] = {"$lt": now}
        
        if past is not None:
            if past:
                filter_query["date_end"] = {"$lt": now}
            else:
                filter_query["date_end"] = {"$gte": now}
        
        # Get total count
        total = await collection.count_documents(filter_query)
        
        # Get events with pagination
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("date_start", 1)
        events = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for event in events:
            event["id"] = str(event["_id"])
        
        return EventList(
            events=[Event(**event) for event in events],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing events: {str(e)}")

@app.get("/events/upcoming", response_model=List[Event])
async def get_upcoming_events(limit: int = Query(10, ge=1, le=100)):
    """Get upcoming events."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        now = datetime.utcnow()
        cursor = collection.find({"date_start": {"$gte": now}}).sort("date_start", 1).limit(limit)
        events = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for event in events:
            event["id"] = str(event["_id"])
        
        return [Event(**event) for event in events]
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting upcoming events: {str(e)}")

@app.get("/events/current", response_model=List[Event])
async def get_current_events():
    """Get currently ongoing events."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        now = datetime.utcnow()
        cursor = collection.find({
            "date_start": {"$lte": now},
            "date_end": {"$gte": now}
        }).sort("date_start", 1)
        events = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for event in events:
            event["id"] = str(event["_id"])
        
        return [Event(**event) for event in events]
        
    except Exception as e:
        logger.error(f"Error getting current events: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting current events: {str(e)}")

@app.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get a specific event by ID."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        event = await collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event["id"] = str(event["_id"])
        return Event(**event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting event: {str(e)}")

@app.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_update: EventUpdate):
    """Update an event."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Get existing event
        existing_event = await collection.find_one({"_id": ObjectId(event_id)})
        if not existing_event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Prepare update data
        update_data = event_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the event
        result = await collection.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get updated event
        updated_event = await collection.find_one({"_id": ObjectId(event_id)})
        updated_event["id"] = str(updated_event["_id"])
        
        return Event(**updated_event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")

@app.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Delete an event."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        result = await collection.delete_one({"_id": ObjectId(event_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return {"message": "Event deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")

@app.get("/events/search/{query}")
async def search_events(query: str, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    """Search events by name or description."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Create search filter
        search_filter = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Get total count
        total = await collection.count_documents(search_filter)
        
        # Get events with pagination
        cursor = collection.find(search_filter).skip(skip).limit(limit).sort("date_start", 1)
        events = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for event in events:
            event["id"] = str(event["_id"])
        
        return EventList(
            events=[Event(**event) for event in events],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error searching events: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching events: {str(e)}")

@app.get("/events/calendar")
async def get_calendar_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get events for calendar view."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Build date filter
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        
        if date_filter:
            filter_query = {"date_start": date_filter}
        else:
            filter_query = {}
        
        cursor = collection.find(filter_query).sort("date_start", 1)
        events = await cursor.to_list(length=1000)
        
        # Convert ObjectId to string and format for calendar
        calendar_events = []
        for event in events:
            event["id"] = str(event["_id"])
            calendar_events.append({
                "id": event["id"],
                "title": event["name"],
                "start": event["date_start"].isoformat(),
                "end": event["date_end"].isoformat(),
                "description": event["description"]
            })
        
        return {"events": calendar_events}
        
    except Exception as e:
        logger.error(f"Error getting calendar events: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting calendar events: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "events"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 