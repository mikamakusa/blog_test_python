from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None

class Post(PostBase):
    id: str
    created_at: datetime
    updated_at: datetime
    html_content: Optional[str] = None

class PostList(BaseModel):
    posts: List[Post]
    total: int 