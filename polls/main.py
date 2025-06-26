from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from bson import ObjectId
import logging
from typing import List, Optional

from config import settings
from database import connect_to_mongo, close_mongo_connection, get_collection
from models import Poll, PollCreate, PollUpdate, PollList, VoteRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog Polls Microservice", version="1.0.0")

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

@app.post("/polls", response_model=Poll)
async def create_poll(poll_data: PollCreate):
    """Create a new poll."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Prepare answers with IDs
        answers = []
        for i, answer in enumerate(poll_data.answers):
            answer_dict = answer.dict()
            answer_dict["id"] = str(ObjectId())
            answer_dict["votes"] = 0
            answers.append(answer_dict)
        
        poll_dict = {
            "question": poll_data.question,
            "is_active": poll_data.is_active,
            "answers": answers,
            "total_votes": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await collection.insert_one(poll_dict)
        poll_dict["id"] = str(result.inserted_id)
        
        return Poll(**poll_dict)
        
    except Exception as e:
        logger.error(f"Error creating poll: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating poll: {str(e)}")

@app.get("/polls", response_model=PollList)
async def list_polls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None)
):
    """List polls with optional filtering."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Build filter
        filter_query = {}
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        # Get total count
        total = await collection.count_documents(filter_query)
        
        # Get polls with pagination
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        polls = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for poll in polls:
            poll["id"] = str(poll["_id"])
        
        return PollList(
            polls=[Poll(**poll) for poll in polls],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing polls: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing polls: {str(e)}")

@app.get("/polls/active", response_model=List[Poll])
async def get_active_polls():
    """Get all active polls."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        cursor = collection.find({"is_active": True}).sort("created_at", -1)
        polls = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for poll in polls:
            poll["id"] = str(poll["_id"])
        
        return [Poll(**poll) for poll in polls]
        
    except Exception as e:
        logger.error(f"Error getting active polls: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting active polls: {str(e)}")

@app.get("/polls/{poll_id}", response_model=Poll)
async def get_poll(poll_id: str):
    """Get a specific poll by ID."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        poll = await collection.find_one({"_id": ObjectId(poll_id)})
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        poll["id"] = str(poll["_id"])
        return Poll(**poll)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting poll: {str(e)}")

@app.put("/polls/{poll_id}", response_model=Poll)
async def update_poll(poll_id: str, poll_update: PollUpdate):
    """Update a poll."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Get existing poll
        existing_poll = await collection.find_one({"_id": ObjectId(poll_id)})
        if not existing_poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        # Prepare update data
        update_data = poll_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the poll
        result = await collection.update_one(
            {"_id": ObjectId(poll_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        # Get updated poll
        updated_poll = await collection.find_one({"_id": ObjectId(poll_id)})
        updated_poll["id"] = str(updated_poll["_id"])
        
        return Poll(**updated_poll)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating poll: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating poll: {str(e)}")

@app.delete("/polls/{poll_id}")
async def delete_poll(poll_id: str):
    """Delete a poll."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        result = await collection.delete_one({"_id": ObjectId(poll_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        return {"message": "Poll deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting poll: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting poll: {str(e)}")

@app.post("/polls/{poll_id}/vote")
async def vote_poll(poll_id: str, vote_data: VoteRequest):
    """Vote on a poll."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        # Get the poll
        poll = await collection.find_one({"_id": ObjectId(poll_id)})
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        if not poll["is_active"]:
            raise HTTPException(status_code=400, detail="Poll is not active")
        
        # Find the answer and update votes
        answer_found = False
        for answer in poll["answers"]:
            if answer["id"] == vote_data.answer_id:
                answer["votes"] += 1
                answer_found = True
                break
        
        if not answer_found:
            raise HTTPException(status_code=404, detail="Answer not found")
        
        # Update total votes
        poll["total_votes"] += 1
        poll["updated_at"] = datetime.utcnow()
        
        # Update the poll in database
        await collection.update_one(
            {"_id": ObjectId(poll_id)},
            {"$set": {
                "answers": poll["answers"],
                "total_votes": poll["total_votes"],
                "updated_at": poll["updated_at"]
            }}
        )
        
        return {"message": "Vote recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error voting on poll: {e}")
        raise HTTPException(status_code=500, detail=f"Error voting on poll: {str(e)}")

@app.get("/polls/{poll_id}/results")
async def get_poll_results(poll_id: str):
    """Get poll results with percentages."""
    try:
        collection = get_collection(settings.mongodb_collection)
        
        poll = await collection.find_one({"_id": ObjectId(poll_id)})
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        total_votes = poll["total_votes"]
        results = []
        
        for answer in poll["answers"]:
            percentage = (answer["votes"] / total_votes * 100) if total_votes > 0 else 0
            results.append({
                "id": answer["id"],
                "text": answer["text"],
                "votes": answer["votes"],
                "percentage": round(percentage, 2)
            })
        
        return {
            "poll_id": str(poll["_id"]),
            "question": poll["question"],
            "total_votes": total_votes,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll results: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting poll results: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "polls"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 