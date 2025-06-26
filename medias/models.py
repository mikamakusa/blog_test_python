from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MediaBase(BaseModel):
    filename: str
    folder: str
    content_type: str
    size: int

class MediaCreate(BaseModel):
    folder: str

class Media(MediaBase):
    id: str
    url: str
    created_at: datetime
    updated_at: datetime

class MediaList(BaseModel):
    medias: list[Media]
    total: int 