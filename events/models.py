from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    date_start: datetime
    date_end: datetime
    call_for_paper_date_start: Optional[datetime] = None
    call_for_paper_date_end: Optional[datetime] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    call_for_paper_date_start: Optional[datetime] = None
    call_for_paper_date_end: Optional[datetime] = None

class Event(EventBase):
    id: str
    created_at: datetime
    updated_at: datetime

class EventList(BaseModel):
    events: list[Event]
    total: int 