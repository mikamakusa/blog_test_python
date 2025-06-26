from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

class AdBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl
    image: str = Field(..., min_length=1)
    is_active: bool = True

class AdCreate(AdBase):
    pass

class AdUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[HttpUrl] = None
    image: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None

class Ad(AdBase):
    id: str
    created_at: datetime
    updated_at: datetime

class AdList(BaseModel):
    ads: list[Ad]
    total: int 