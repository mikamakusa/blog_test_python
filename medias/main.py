from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from datetime import datetime
import logging
import os
from typing import List, Optional

from config import settings
from models import Media, MediaList
from minio_client import minio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog Medias Microservice", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for media metadata (in production, use a database)
media_storage = {}

@app.post("/upload", response_model=Media)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("general")
):
    """Upload a file to MinIO."""
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        
        # Upload to MinIO
        object_name = await minio_client.upload_file(
            file_content,
            filename,
            folder,
            file.content_type
        )
        
        # Store metadata
        media_id = f"{folder}_{timestamp}_{file.filename}"
        media_data = {
            "id": media_id,
            "filename": filename,
            "folder": folder,
            "content_type": file.content_type,
            "size": len(file_content),
            "url": minio_client.get_file_url(object_name),
            "object_name": object_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        media_storage[media_id] = media_data
        
        return Media(**media_data)
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/files", response_model=MediaList)
async def list_files(
    folder: Optional[str] = Query(None, description="Filter by folder"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List uploaded files."""
    try:
        filtered_medias = []
        
        for media_id, media_data in media_storage.items():
            if folder is None or media_data["folder"] == folder:
                filtered_medias.append(media_data)
        
        # Apply pagination
        total = len(filtered_medias)
        paginated_medias = filtered_medias[skip:skip + limit]
        
        return MediaList(
            medias=[Media(**media) for media in paginated_medias],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.get("/files/{media_id}", response_model=Media)
async def get_file(media_id: str):
    """Get file information by ID."""
    if media_id not in media_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    media_data = media_storage[media_id]
    return Media(**media_data)

@app.get("/files/{media_id}/download")
async def download_file(media_id: str):
    """Download a file by ID."""
    if media_id not in media_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    media_data = media_storage[media_id]
    download_url = minio_client.get_file_url(media_data["object_name"])
    
    return RedirectResponse(url=download_url)

@app.delete("/files/{media_id}")
async def delete_file(media_id: str):
    """Delete a file by ID."""
    if media_id not in media_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        media_data = media_storage[media_id]
        
        # Delete from MinIO
        await minio_client.delete_file(media_data["object_name"])
        
        # Remove from storage
        del media_storage[media_id]
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.get("/folders")
async def list_folders():
    """List all folders."""
    folders = set()
    for media_data in media_storage.values():
        folders.add(media_data["folder"])
    
    return {"folders": list(folders)}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "medias"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 